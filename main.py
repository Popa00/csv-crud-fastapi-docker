from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import csv
import os
import threading
from typing import List, Optional
import re
from contextlib import asynccontextmanager

#app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Applicazione in avvio...")
    initialize_csv()
    print("File CSV inizializzato.")
    yield
    print("Applicazione in chiusura...")


app = FastAPI(lifespan=lifespan)

#definisco lo schema dati
class Utente(BaseModel):
    id: int = Field(...)
    nome: str = Field(..., min_length=1)
    cognome: str = Field(..., min_length=1)
    codice_fiscale: str = Field(..., min_length=16, max_length=16)

class RispostaUtente(BaseModel):
    id: int
    nome: str
    cognome: str
    codice_fiscale: str

# Configurazione del file CSV
CSV_FILE = "data.csv"
CSV_HEADERS = ["id", "nome", "cognome", "codice_fiscale"]

#serve ad inizializzare il lock, utile se ci sono più threads concorrenti
file_lock = threading.Lock()

#creo il file csv se non esiste
def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)      #scrive gli headers nel file
            writer.writerow(CSV_HEADERS)

#funzione per leggere il file csv
def read_csv() -> List[dict]:
    initialize_csv()
    letti = []
    try:
        with open(CSV_FILE, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['id']:  
                    letti.append({
                        'id': int(row['id']),
                        'nome': row['nome'],
                        'cognome': row['cognome'],
                        'codice_fiscale': row['codice_fiscale']
                    })
    except FileNotFoundError:
        pass
    return letti

#funzione per scrivere sul file
def write_csv(letti: List[dict]):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for i in letti:
            writer.writerow(i)

#funzione per la ricerca per id
def find_by_id(item_id: int) -> Optional[dict]:
    letti = read_csv()
    for i in letti:
        if i['id'] == item_id:
            return i
    return None

#funzione per controllare che il codice fiscale sia valido
def vale_codfiscale(codice_fiscale: str) -> bool:
    if len(codice_fiscale) != 16:
        return False
     # Controllo caratteri e formato
    if not codice_fiscale.isalnum() or not codice_fiscale.isupper():
        return False
    
    # Pattern: 6 lettere + 2 numeri + 1 lettera + 2 numeri + 1 lettera + 3 caratteri + 1 lettera
    pattern = r'^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$'
    if not re.match(pattern, codice_fiscale):
        return False
    return True


########################################################################################
#inizio chiamate#

@app.get('/items/count')
async def conta():
    with file_lock:
        letti = read_csv()
        count = len(letti)
        return {'count': count}


@app.post('/items/', response_model=RispostaUtente, status_code=status.HTTP_201_CREATED)
async def create_item(item: Utente):
    with file_lock:
        if not vale_codfiscale(item.codice_fiscale):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Codice fiscale non valido')
        existing_item = find_by_id(item.id)
        if existing_item:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Esiste già un elemento con id: {item.id}')
        
        letti = read_csv()
        for i in letti:
            if i['codice_fiscale'] == item.codice_fiscale:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Esiste già un elemento con questo codice fiscale')
        
        nuovo_item = item.model_dump()  
        letti.append(nuovo_item)
        write_csv(letti)

        return RispostaUtente(**nuovo_item)

@app.get('/items/', response_model=List[RispostaUtente])
async def get_all_items():
    with file_lock:
        letti = read_csv()
        return [RispostaUtente(**i) for i in letti]
    

@app.get('/items/{id}', response_model=RispostaUtente)
async def get_item(id: int):
    with file_lock:
        item = find_by_id(id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'L\'ID {id} non è stato trovato')
        return RispostaUtente(**item)
    
@app.put('/items/{id}', response_model=RispostaUtente)
async def modifica(id: int, item: Utente):
    with file_lock:
        if not vale_codfiscale(item.codice_fiscale):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Il codice fiscale non è valido')
        if item.id != id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='L\'ID non corrisponde')
        
        letti = read_csv()

        for i in letti:
            if i['codice_fiscale'] == item.codice_fiscale and i['id'] != id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Esiste già un elemento con questo codice fiscale')
            if i['id'] == id:
                letti.remove(i)
                letti.append(item.model_dump())
                write_csv(letti)
                return RispostaUtente(**item.model_dump())
            
@app.delete('/items/{id}')
async def elimina(id: int):
    with file_lock:
        letti = read_csv()
        for i in letti:
            if id == i['id']:
                letti.remove(i)
                break
        write_csv(letti)
        return {'message': 'Elemento eliminato con successo'}
    

    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)