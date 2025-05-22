import csv
import random
from pyproj import Transformer
import math


def get_random_gemeinde():
    # Zufällige Gemeinde auswählen
    random_gemeinde = random.choice(_gemeinden_cache)
    return random_gemeinde

_gemeinden_cache =[]

def lade_gemeinden():
    global _gemeinden_cache
    if not _gemeinden_cache:
        with open("data/Gemeinden_CH.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            _gemeinden_cache = [row for row in reader if row["E"] and row["N"]]

# Funktion zum Abrufen einer zufälligen Gemeinde
def get_random_gemeinde():
    if not _gemeinden_cache:
        lade_gemeinden()
    return random.choice(_gemeinden_cache)


def wgs84_to_lv95(lat, lon):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    e, n = transformer.transform(lon, lat)
    return round(e, 2), round(n, 2)


def lv95_to_wgs84(e, n):
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e, n)
    return lat, lon


def distanz_berechnen_lv95(coords, gemeinde):
    e_lv95, n_lv95 = wgs84_to_lv95(coords[0], coords[1])
    user_coords_lv95 = (e_lv95, n_lv95)
    ziel_coords_lv95 = (float(gemeinde["E"]), float(gemeinde["N"]))
    e1, n1 = user_coords_lv95
    e2, n2 = ziel_coords_lv95
    distanz_m = math.sqrt((e2 - e1)**2 + (n2 - n1)**2)
    return round(distanz_m / 1000, 2)


