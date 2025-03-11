import csv
import pandas as pd
import requests
import json

# Konfiguration
API_URL = "https://verhuetungsmittel-eigenschaften.wikibase.cloud/w/api.php"
USERNAME = "Nune Arazyan"
PASSWORD = "XXXXXXX" # das wirkliche Passwort wurde hier durch X ersetzt, aus diesem Grund ist der Code nicht reproduzierbar 
CSV_FILE_CONTRACEPION = "contraception_data.csv" 
CSV_FILE_PUBLICATIONS = "publications_pubmed_data.csv" 

session = requests.Session()

# Login
def get_login_token():
    response = session.get(API_URL, params={
        "action": "query",
        "meta": "tokens",
        "type": "login",
        "format": "json"
    })
    return response.json()["query"]["tokens"]["logintoken"]

def login():
    token = get_login_token()
    
    response = session.post(API_URL, data={
        "action": "login",
        "lgname": USERNAME,
        "lgpassword": PASSWORD,
        "lgtoken": token,
        "format": "json"
    })
    
    return response.json()

# Bearbeitung und Abrufen des Edit-Tokens
def get_edit_token():
    response = session.get(API_URL, params={
        "action": "query",
        "meta": "tokens",
        "format": "json"
    })
    return response.json()["query"]["tokens"]["csrftoken"]

# Erstellung von Entitäten bzw. Instanzen
def create_entity(label, description, token):
    data = {
        "labels": {
            "de": {"language": "de", "value": label}
        },
        "descriptions": {
            "de": {"language": "de", "value": description}
        }
    }

    response = session.post(API_URL, data={
        "action": "wbeditentity",
        "new": "item",
        "data": json.dumps(data),
        "format": "json",
        "token": token
    })

    return response.json()

# Erstellung von Entitäten, die als Oberklassen gelten, samt Beschreibungen
def create_predefined_entities(edit_token):
    entities = {
        "Verhütungsmittel": "Verhütungsmittel oder Verhütungsmethoden dienen dem Schutz von ungewollter Schwangerschaft und sexuell übertragbaren Krankheiten.",
        "Geschlecht": "Geschlechter, die theoretisch die jeweilige Verhütungsmethode benutzen können.",
        "Material des Verhütungsmittels": "Materialien und Stoffe, aus denen das Verhütungsmittel besteht.",
        "Art des Verhütungsmittels": "Es gibt chemische, hormonelle, mechanische, natürliche und operative Verhütungsmittel.",
        "Häufigkeit der Annahme / Applikation": "Wie oft muss ein Verhütungsmittel eingenommen oder angewendet werden.",
        "Effizienzmaße": "Wie hoch sind Effizienz, Pearl-Index und Fehlerquote bei Anwendung."
    }
    
    for label, description in entities.items():
        result = create_entity(label, description, edit_token)
        print(f"Entität für '{label}' erstellt: {result}")

# Erstellung von Entitäten für einzigartige Werte in Zellen der entsprechenden Spalten 
def create_entity_uniq(label, edit_token):
    data = {
        "action": "wbeditentity",
        "new": "item",
        "data": json.dumps({
            "labels": {
                "de": {
                    "language": "de",
                    "value": label
                }
            }
        }),
        "token": edit_token,
        "format": "json"
    }
    
    response = session.post(API_URL, data=data)
    return response.json()

# Login
login_response = login()
print("Login Response:", login_response)

if login_response.get('login', {}).get('result') == 'Success':
    print("Login erfolgreich.")
    
    edit_token = get_edit_token()

    # Erstellung von Oberklassen
    create_predefined_entities(edit_token)

    # Speicherung der einzigartigen Einträge
    unique_entries = set()

    # Einlesen der CSV-Datei mit Verhütungsmitteln und Erstellen von Entitäten
    with open(CSV_FILE_CONTRACEPION, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=",")
        
        for row in reader:
            # Erstellen der Entität für Verhütungsmittel (Lde) samt ihren Beschreibungen (Dde)
            label = row["Lde"]
            description = row["Dde"]
            if label:  
                result = create_entity(label, description, edit_token)
                print(f"Entität für '{label}' erstellt: {result}")

            # Einzigartige Einträge aus entsprechenden Spalten
            for column in ['P3_1', 'P3_2', 'P3_3', 'P4_1', 'P4_2', 'P5_1', 'P5_2', 'P5_3', 'P11', 'P12_1', 'P12_2']:
                value = row.get(column)
                if value:  
                    unique_entries.add(value.strip())
    
    # Einlesen der CSV-Datei mit Publikationen und Erstellen von Entitäten
    with open(CSV_FILE_PUBLICATIONS, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=",")
        
        for row in reader:
            # Erstellen der Entität für Publikationen (Lde) samt ihren Beschreibungen (Dde)
            label = row["Lde"]
            description = row["Dde"]
            if label:  
                result = create_entity(label, description, edit_token)
                print(f"Entität für '{label}' erstellt: {result}")

    # Erstellen der einzigartigen Entitäten
    print(f"Einzigartige Einträge ({len(unique_entries)}): {unique_entries}")
    
    for entry in unique_entries:
        create_response = create_entity_uniq(entry, edit_token)
        print(f"Entität erstellt für: {entry}, Response: {create_response}")

    print("Alle Entitäten wurden erfolgreich erstellt.")

else:
    print("Login fehlgeschlagen:", login_response)