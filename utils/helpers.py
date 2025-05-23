import csv
import random
from pyproj import Transformer
import math

_spiel_runden_gemeinden = []
_spiel_runde_index = 0

def lade_csv_daten(datei):
    with open(f"data/{datei}", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        first_row = next(reader, None)
        if not first_row or "E" not in first_row or "N" not in first_row:
            raise ValueError(f"CSV-Datei '{datei}' hat nicht die erwarteten Spalten 'E' und 'N'.")
        f.seek(0)
        reader = csv.DictReader(f, delimiter=";")
        unique_coords = set()
        unique_rows = []
        for row in reader:
            coords = (row["E"], row["N"])
            if coords not in unique_coords:
                unique_coords.add(coords)
                unique_rows.append(row)
        return unique_rows

def vorbereite_spiel_runden(anzahl=10, datei="Ortschaften.csv"):
    global _spiel_runden_gemeinden, _spiel_runde_index
    daten = lade_csv_daten(datei)
    if len(daten) < anzahl:
        raise ValueError(f"Nicht genügend Einträge in {datei} für {anzahl} Runden")
    _spiel_runden_gemeinden = random.sample(daten, anzahl)
    _spiel_runde_index = 0

def get_next_gemeinde():
    global _spiel_runde_index
    if _spiel_runde_index < len(_spiel_runden_gemeinden):
        gemeinde = _spiel_runden_gemeinden[_spiel_runde_index]
        _spiel_runde_index += 1
        return gemeinde
    return None

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
    ziel_coords_lv95 = (float(gemeinde["E"]), float(gemeinde["N"]))
    distanz_m = math.sqrt((ziel_coords_lv95[0] - e_lv95)**2 + (ziel_coords_lv95[1] - n_lv95)**2)
    return round(distanz_m / 1000, 2)
