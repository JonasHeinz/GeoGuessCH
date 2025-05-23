import csv
import os

LEADERBOARD_FILE = "leaderboard.csv"

def lade_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        daten = list(reader)
    daten.sort(key=lambda x: float(x["Kilometer"]))  # kleinste zuerst
    return daten

def schreibe_leaderboard(name, kilometer):
    daten = lade_leaderboard()
    daten.append({"Name": name, "Kilometer": str(kilometer)})
    daten.sort(key=lambda x: float(x["Kilometer"]))  # kleinste zuerst
    daten = daten[:10]  # Nur Top 10
    with open(LEADERBOARD_FILE, 'w', newline='') as csvfile:
        fieldnames = ["Name", "Kilometer"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(daten)

def zeige_leaderboard():
    daten = lade_leaderboard()
    if not daten:
        print("Keine Einträge im Leaderboard.")
        return

    print("=== Leaderboard Top 10 Scores ===")
    for i, eintrag in enumerate(daten, start=1):
        name = eintrag["Name"]
        kilometer = eintrag["Kilometer"]
        print(f"{i}. {name}: {kilometer} Kilometer")