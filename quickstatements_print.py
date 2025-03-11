import csv
import requests
from bs4 import BeautifulSoup
import re

CSV_FILE_CONTRACEPION = "contraception_data.csv" 
CSV_FILE_PUBLICATIONS = "publications_pubmed_data.csv" 
WIKIBASE_API_URL = "https://verhuetungsmittel-eigenschaften.wikibase.cloud/w/api.php"

# Funktion zur Suche nach Wikibase-IDs
def search_wikibase_entity(entity_name):
    params = {
        'action': 'wbsearchentities',
        'search': entity_name,
        'language': 'de',
        'format': 'json',
        'limit': 1  # Nur die erste Übereinstimmung wird zurückgegeben
    }
    
    response = requests.get(WIKIBASE_API_URL, params=params)
    data = response.json()
    
    if 'search' in data and data['search']:
        return data['search'][0]['id']
    return None

# Definition der Oberklassen-IDs
P2_Q1 = "Q1"  # Oberklasse für LDE
P2_Q2 = "Q2"  # Oberklasse für Geschlecht
P2_Q3 = "Q3"  # Oberklasse für Material des Verhütungsmittels
P2_Q4 = "Q4"  # Oberklasse für Art des Verhütungsmittels
P2_Q5 = "Q5"  # Oberklasse für Häufigkeit der Anahme

# QuickStatements-Vorlagen
quickstatements = []

# Einzigartige Einträge in den Spalten extrahieren
unique_entries = {
    "LDE": set(),
    "P3": set(), # Geschlecht
    "P4": set(), # Art des Verhütungsmittels
    "P11": set(), # Häufigkeit der Anahme
    "P5": set() # Material des Verhütungsmittels
}

# CSV_FILE_PUBLICATIONS-Daten einlesen und speichern
publications_data = []
with open(CSV_FILE_PUBLICATIONS, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file, delimiter=",")
    for row in reader:
        publications_data.append(row)

# CSV_FILE_CONTRACEPION-Daten einlesen
with open(CSV_FILE_CONTRACEPION, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file, delimiter=",")
    
    for row in reader:
        # Einträge für LDE
        if row['Lde']:
            lde_entry = row['Lde'].strip()
            unique_entries["LDE"].add(lde_entry)
        
        # Einträge für Geschlecht
        for column in ['P3_1', 'P3_2', 'P3_3']:
            if row[column]:
                p2_entry = row[column].strip()
                unique_entries["P3"].add(p2_entry)
        
        # Einträge für Art des Verhütungsmittels
        for column in ['P4_1', 'P4_2']:
            if row[column]:
                p3_entry = row[column].strip()
                unique_entries["P4"].add(p3_entry)
        
        # Einträge für Häufigkeit der Anahme
        if row['P11']:
            p10_entry = row['P11'].strip()
            unique_entries["P11"].add(p10_entry)
        
        # Einträge für Material des Verhütungsmittels
        for column in ['P5_1', 'P5_2', 'P5_3']:
            if row[column]:
                p4_entry = row[column].strip()
                unique_entries["P5"].add(p4_entry)

# Suche nach Wikibase-IDs und Erstellen der QuickStatements
for entry in unique_entries["LDE"]:
    wikibase_id = search_wikibase_entity(entry)
    if wikibase_id:
        quickstatements.append(f'{wikibase_id}|P2|{P2_Q1} /* Verknüpfung Verhütung mit "Verhütungsmittel" */')
        quickstatements.append(f'{P2_Q1}|P25|{wikibase_id} /* inversive Verknüpfung" */')

for entry in unique_entries["P3"]:
    wikibase_id = search_wikibase_entity(entry)
    if wikibase_id:
        quickstatements.append(f'{wikibase_id}|P2|{P2_Q2} /* Verknüpfung einzelner "Geschlechter mit Geschlecht" */')
        quickstatements.append(f'{P2_Q2}|P25|{wikibase_id} /* inversive Verknüpfung" */')

for entry in unique_entries["P4"]:
    wikibase_id = search_wikibase_entity(entry)
    if wikibase_id:
        quickstatements.append(f'{wikibase_id}|P2|{P2_Q4} /* Verknüpfung einzelner Arten mit "Art des Verhütungsmittels" */')
        quickstatements.append(f'{P2_Q4}|P25|{wikibase_id} /* inversive Verknüpfung" */')

for entry in unique_entries["P5"]:
    wikibase_id = search_wikibase_entity(entry)
    if wikibase_id:
        quickstatements.append(f'{wikibase_id}|P2|{P2_Q3} /* Verknüpfung einzelner Materialien mit "Material des Verhütungsmittels" */')
        quickstatements.append(f'{P2_Q3}|P25|{wikibase_id} /* inversive Verknüpfung" */')

for entry in unique_entries["P11"]:
    wikibase_id = search_wikibase_entity(entry)
    if wikibase_id:
        quickstatements.append(f'{wikibase_id}|P2|{P2_Q5} /* Verknüpfung einzelner Angaben mit "Häufigkeit der Einnahme / Applikation" */')
        quickstatements.append(f'{P2_Q5}|P25|{wikibase_id} /* inversive Verknüpfung" */')

# QuickStatements für Lde-Verknüpfungen mit allen Properties für Verhütungsmittel
with open(CSV_FILE_CONTRACEPION, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file, delimiter=",")
    for row in reader:
        lde_label = row["Lde"].strip()
        lde_qid = search_wikibase_entity(lde_label) if lde_label else None

        if lde_qid:
            for column, value in row.items():
                if column.startswith("P") and value and value.strip():
                    match = re.match(r"^P\d{1,2}", column) # für den Fall, dass die P-ID aus 2 Zahlen besteht
                    property_id = match.group(0) if match else column
                    value = value.strip()
                    
                    # Suche nach Q-ID für den entsprechenden Wert
                    value_qid = search_wikibase_entity(value)

                    # Falls kein QID gefunden wurde, Klartext-Wert nutzen
                    value_output = value_qid if value_qid else f'"{value}"'

                    statement = f'{lde_qid}|{property_id}|{value_output}'
                    
                    # Einfügen der Source-Referenz (S24), falls Bedingungen dafür erfüllt
                    for pub_row in publications_data:
                        # Bedingungen: Verhütungsmittel in P22 entspricht dem Verhütungsmittel in der Aussage UND die P-ID in der Spalte "Source-Prop-Ent" entspricht der P-ID in der Aussage
                        if pub_row["P22"].strip() == lde_label and pub_row["Source-Prop-Ent"].strip() == property_id:
                            source_entity_name = pub_row["Lde"].strip()
                            source_qid = search_wikibase_entity(source_entity_name)
                            if source_qid:
                                statement += f'|S24|{source_qid}'  # Source-Angabe vor dem Kommentar einfügen

                    # Kommentar erst am Ende
                    statement += f' /* {lde_label} → {property_id} → {value} */'
                    
                    quickstatements.append(statement)

# QuickStatements für Lde-Verknüpfungen mit allen Properties für Metadaten der Publikationen
with open(CSV_FILE_PUBLICATIONS, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file, delimiter=",")

    for row in reader:
        if "Lde" in row and row["Lde"]:
            lde_label = row["Lde"].strip()
            lde_qid = search_wikibase_entity(lde_label) if lde_label else None

            if lde_qid:
                for column, value in row.items():
                    if column.startswith("P") and value and value.strip():
                        match = re.match(r"^P\d{1,2}", column)
                        property_id = match.group(0) if match else column
                        value = value.strip()

                        value_qid = search_wikibase_entity(value)

                        value_output = value_qid if value_qid else f'"{value}"'

                        quickstatements.append(f'{lde_qid}|{property_id}|{value_output}/* {lde_label} → {property_id} → {value} */')

# QuickStatements in einer Output-Datei speichern
OUTPUT_FILE = "quickstatements.txt"

if quickstatements:
    with open(OUTPUT_FILE, mode="w", encoding="utf-8") as file:
        file.write("\n".join(quickstatements))
    print(f"QuickStatements wurden in '{OUTPUT_FILE}' gespeichert.")
else:
    print("Keine QuickStatements generiert.")