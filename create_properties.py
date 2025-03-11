import csv
import requests
import json

# Konfiguration
API_URL = "https://verhuetungsmittel-eigenschaften.wikibase.cloud/w/api.php"
USERNAME = "Nune Arazyan"
PASSWORD = "XXXXXXX" # das wirkliche Passwort wurde hier durch X ersetzt, aus diesem Grund ist der Code nicht reproduzierbar 
CSV_FILE = "properties.csv" 

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

# Bearbeitung
def get_edit_token():
    response = session.get(API_URL, params={
        "action": "query",
        "meta": "tokens",
        "format": "json"
    })
    return response.json()["query"]["tokens"]["csrftoken"]

# Erstellung von Properties
def create_property(label, description, data_type, token):
    data = {
        "labels": {
            "de": {"language": "de", "value": label}
        },
        "descriptions": {
            "de": {"language": "de", "value": description}
        },
        "datatype": data_type
    }

    response = session.post(API_URL, data={
        "action": "wbeditentity",
        "new": "property",
        "data": json.dumps(data),  
        "format": "json",
        "token": token
    })

    return response.json()

# Login
login_response = login()
print("Login Response:", login_response)

# Edit-Token abrufen
edit_token = get_edit_token()

# Einlesen der CSV-Datei und Erstellen von Properties
with open(CSV_FILE, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file, delimiter=",")

    for row in reader:
        label = row["label"]
        description = row["description"]
        data_type = row["data_type"]
        
        result = create_property(label, description, data_type, edit_token)
        print("Property created:", result)

print("Alle Properties wurden eingefügt.")