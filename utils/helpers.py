import csv
import random
from pyproj import Transformer
import math


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



def wgs84_to_lv95(lat, lon):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    e, n = transformer.transform(lon, lat)
    return round(e, 2), round(n, 2)

def distanz_berechnen_lv95(coords, gemeinde):
    e_lv95, n_lv95 = wgs84_to_lv95(coords[0], coords[1])
    user_coords_lv95 = (e_lv95, n_lv95)
    ziel_coords_lv95 = (float(gemeinde["E"]), float(gemeinde["N"]))
    e1, n1 = user_coords_lv95
    e2, n2 = ziel_coords_lv95
    distanz_m = math.sqrt((e2 - e1)**2 + (n2 - n1)**2)
    return round(distanz_m / 1000, 2)


