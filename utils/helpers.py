import csv
import random
from pyproj import Transformer
import math

# Caches
_gemeinden_cache = []
_spiel_runden_gemeinden = []

def lade_gemeinden():
    global _gemeinden_cache
    if not _gemeinden_cache:
        with open("data/Gemeinden_CH.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            _gemeinden_cache = [row for row in reader if row["E"] and row["N"]]

_spiel_runden_gemeinden = []
_spiel_runde_index = 0

def vorbereite_spiel_runden(anzahl=10):
    global _spiel_runden_gemeinden, _spiel_runde_index
    lade_gemeinden()
    _spiel_runden_gemeinden = random.sample(_gemeinden_cache, anzahl)
    _spiel_runde_index = 0

def get_next_gemeinde():
    global _spiel_runde_index
    if _spiel_runde_index < len(_spiel_runden_gemeinden):
        gemeinde = _spiel_runden_gemeinden[_spiel_runde_index]
        _spiel_runde_index += 1
        return gemeinde
    return None  # Keine weiteren Gemeinden mehr

# Koordinatentransformationen
def wgs84_to_lv95(lat, lon):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    e, n = transformer.transform(lon, lat)
    return round(e, 2), round(n, 2)

def lv95_to_wgs84(e, n):
    transformer = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(e, n)
    return lat, lon

# Distanzberechnung
def distanz_berechnen_lv95(coords, gemeinde):
    e_lv95, n_lv95 = wgs84_to_lv95(coords[0], coords[1])
    user_coords_lv95 = (e_lv95, n_lv95)
    ziel_coords_lv95 = (float(gemeinde["E"]), float(gemeinde["N"]))
    e1, n1 = user_coords_lv95
    e2, n2 = ziel_coords_lv95
    distanz_m = math.sqrt((e2 - e1)**2 + (n2 - n1)**2)
    return round(distanz_m / 1000, 2)

# Beim Start vorbereiten:
lade_gemeinden()
vorbereite_spiel_runden(10)
