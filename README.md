# csv-crud-fastapi-docker
Progetto richiesto per colloquio Social Thingum.

Il progetto sviluppato ha come obiettivo la gestione backend delle operazioni CRUD su un file CSV.

Tramite l'utilizzo di fastAPI e uvicorn permette quindi la creazione, lettura, modifica ed eliminazione di dati, in questo caso nome, cognome, id e codice fiscale.

Il progetto si serve anche di Docker, per creare l'immagine docker usare il comando: 
docker build -t fastapi-app .
Per avviare il container:
docker run -d -p 8000:8000 --name nome_container fastapi-app
