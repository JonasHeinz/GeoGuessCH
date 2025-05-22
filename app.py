from shiny import App, ui, reactive, render
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, Marker, TileLayer, Icon, Polyline
from utils.helpers import get_random_gemeinde, distanz_berechnen_lv95, lv95_to_wgs84, lade_gemeinden
import asyncio
import json
from ipyleaflet import GeoJSON
import geopandas as gpd
import shapely





async def lade_naechste_gemeinde():
    await asyncio.sleep(1)  # 1 Sekunde warten
    random_gemeinde.set(get_random_gemeinde())
    clicked_coords.set(None)  # Klick zurücksetzen

# Reaktive Zustände
player_name = reactive.Value("")
clicked_coords = reactive.Value(None)
game_state = reactive.Value("start")
random_gemeinde = reactive.Value(None)
count = reactive.Value(0)
total_distance = reactive.Value(0)
distance = reactive.Value(0)
map_widget = reactive.Value(None)

# UI
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(
            """
            body, html {
                height: 100%;
                margin: 0;
                overflow: hidden;
            }
            #background_map {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                filter: blur(4px) brightness(0.9);
                z-index: -1;
            }
            .center-box {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background-color: rgba(255, 255, 255, 0.95);
                padding: 40px;
                box-shadow: 0px 0px 25px rgba(0,0,0,0.3);
                border-radius: 15px;
                min-width: 300px;
                text-align: center;
                z-index: 10;
            }
            .leaflet-container {
            cursor: crosshair !important;
            }
            """
        )
    ),
    output_widget("background_map"),
    ui.output_ui("main_ui")
)

def server(input, output, session):
    lade_gemeinden()

    # Hintergrundkarte
    background = Map(center=(46.8, 8.3), zoom=7,
                     scroll_wheel_zoom=False, zoom_control=False)
    background.interaction = False
    register_widget("background_map", background)

    @output
    @render.ui
    def main_ui():
        if game_state.get() == "start":
            return [
                ui.div(
                    {"class": "center-box"},
                    ui.h2("Swiss GeoGuess"),
                    ui.input_text("name_input", "", placeholder="Gib deinen Namen ein..."),
                    ui.input_action_button("start_btn", "Start", class_="btn btn-primary mt-3"),
                )
            ]
        elif game_state.get() == "end":
            return [
                ui.div(
                    {"class": "center-box"},
                    ui.h3("Swiss GeoGuess"),
                    ui.h4(f"Herzlichen Glückwunsch, {player_name.get()}!"),
                    ui.h5("Du hast das Spiel beendet!"),
                    ui.br(),
                    ui.h4("Gesamtdifferenz:"),
                    ui.output_text("total_distance_text"),
                    ui.input_action_button("end_btn", "Spiel beenden", class_="btn btn-primary mt-3"),
                )
            ]
        else:
            return [
                ui.h3(f"Suche Ort: {random_gemeinde.get()['Gemeindename']}"),
                output_widget("map_widget"),
                ui.output_text("coord_text"),
            ]

    @reactive.Effect
    @reactive.event(input.start_btn)
    def start_game():
        name = input.name_input().strip()
        if name:
            player_name.set(name)
            game_state.set("game")
            random_gemeinde.set(get_random_gemeinde())
            count.set(0)
            total_distance.set(0)
            distance.set(0)
            clicked_coords.set(None)
            map_widget.set(None)  # Karte neu aufbauen beim Spielstart

    @reactive.Effect
    @reactive.event(input.end_btn)
    def end_game():
        game_state.set("start")
        random_gemeinde.set(None)
        count.set(0)
        total_distance.set(0)
        distance.set(0)
        clicked_coords.set(None)
        map_widget.set(None)  # Karte entfernen zum Neustart

    @reactive.Effect
    def setup_game():
        if game_state.get() != "game" or map_widget.get() is not None:
            return

        with open("data/kantonsgrenzen_2d.geojson", "r", encoding="utf-8") as f:
            data = json.load(f)

        kantonsgrenzen = GeoJSON(
            data=data,
            name="Kantonsgrenzen",
            interactive=False,
            style={
                "color": "black",
                "weight": 0.5,
                "fillOpacity": 0.0,
            },
            highlight_function=lambda x: {
                "weight": 0.5,
                "color": "black",
                "fillOpacity": 0.0
            }
        )

        esri_shaded = TileLayer(
            url="https://tiles.stadiamaps.com/tiles/stamen_terrain_background/{z}/{x}/{y}{r}.png",
            name="Stamen Terrain"
        )

        m = Map(
            center=(46.8, 8.3),
            zoom=7,
            min_zoom=7,
            max_zoom=13,
            scroll_wheel_zoom=True,
            max_bounds=[[45.5, 5.5], [47.9, 10.5]]
        )

        m.add_layer(kantonsgrenzen)
        m.add_layer(esri_shaded)

        red_icon = Icon(icon_url="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
                        icon_size=[25, 41], icon_anchor=[12, 41])
        ziel_marker = Marker(location=(0, 0), icon=red_icon, draggable=False, opacity=0.9)

        marker = Marker(location=(46.8, 8.3), draggable=True)
        m.add_layer(marker)

        linie = Polyline(locations=[], color="red", weight=4)
        m.add_layer(linie)

        def on_map_click(**kwargs):
            if kwargs.get("type") == "click":
                if count.get() < 5:  # Beispiel: max 5 Versuche
                    latlng = kwargs.get("coordinates")
                    if not latlng or not random_gemeinde.get():
                        return

                    marker.location = latlng
                    clicked_coords.set((round(latlng[0], 5), round(latlng[1], 5)))

                    # Berechnung der Distanz
                    distanz = distanz_berechnen_lv95(clicked_coords.get(), random_gemeinde.get())
                    distance.set(distanz)
                    total_distance.set(total_distance.get() + distanz)

                    ziel_e = float(random_gemeinde.get()["E"])
                    ziel_n = float(random_gemeinde.get()["N"])
                    ziel_lat, ziel_lon = lv95_to_wgs84(ziel_e, ziel_n)

                    ziel_marker.location = (ziel_lat, ziel_lon)
                    if ziel_marker not in m.layers:
                        m.add_layer(ziel_marker)

                    linie.locations = [marker.location, ziel_marker.location]

                    # Lade nächste Gemeinde nach kurzer Pause
                    asyncio.create_task(lade_naechste_gemeinde())
                    count.set(count.get() + 1)
                else:
                    game_state.set("end")

        m.on_interaction(on_map_click)
        register_widget("map_widget", m)
        map_widget.set(m)

    @output
    @render.text
    def total_distance_text():
        return f"{total_distance.get():.2f} km"

    @output
    @render.text
    def coord_text():
        if not clicked_coords.get():
            return "Klicke auf die Karte, um deine Schätzung abzugeben."
        return f"Distanz zur Lösung: {distance.get():.2f} km"

# App starten
app = App(app_ui, server)
