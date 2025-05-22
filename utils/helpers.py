import csv
import random


def get_random_gemeinde():
    # CSV-Datei laden (Trennzeichen ; beachten)
    gemeinden = []
    with open("data/Gemeinden_CH.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row["E"] and row["N"]:
                gemeinden.append(row)

    # Zufällige Gemeinde auswählen
    random_gemeinde = random.choice(gemeinden)
    return random_gemeinde