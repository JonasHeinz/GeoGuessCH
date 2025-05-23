import csv
import os

LEADERBOARD_DIR = "data/leaderboards"

def get_leaderboard_file(modus):
    # Sicherstellen, dass der Ordner existiert
    os.makedirs(LEADERBOARD_DIR, exist_ok=True)
    return os.path.join(LEADERBOARD_DIR, f"leaderboard_{modus}.csv")

def lade_leaderboard(modus):
    datei = get_leaderboard_file(modus)
    if not os.path.exists(datei):
        return []
    with open(datei, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        daten = list(reader)
    daten.sort(key=lambda x: float(x["Kilometer"]))  # kleinste zuerst
    return daten

def schreibe_leaderboard(name, kilometer, modus):
    daten = lade_leaderboard(modus)
    daten.append({"Name": name, "Kilometer": str(kilometer)})
    daten.sort(key=lambda x: float(x["Kilometer"]))  # kleinste zuerst
    daten = daten[:10]  # Nur Top 10
    with open(get_leaderboard_file(modus), 'w', newline='') as csvfile:
        fieldnames = ["Name", "Kilometer"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(daten)

def zeige_leaderboard(modus):
    daten = lade_leaderboard(modus)
    if not daten:
        print(f"Keine Einträge im Leaderboard für Modus '{modus}'.")
        return

    print(f"=== Leaderboard Top 10 ({modus}) ===")
    for i, eintrag in enumerate(daten, start=1):
        name = eintrag["Name"]
        kilometer = eintrag["Kilometer"]
        print(f"{i}. {name}: {kilometer} km")
