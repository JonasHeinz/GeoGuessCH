from shiny import App, ui, reactive, render
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, Marker, TileLayer
from utils.helpers import get_random_gemeinde, wgs84_to_lv95, distanz_berechnen_lv95
from ipyleaflet import GeoJSON
import json
import asyncio

async def lade_naechste_gemeinde():
    await asyncio.sleep(3)  # 3 Sekunden warten
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
            """
        )
    ),
    ui.output_ui("main_ui")
)

# Server
def server(input, output, session):

    # Hintergrundkarte auf Startseite
    background = Map(center=(46.8, 8.3), zoom=7, scroll_wheel_zoom=False, zoom_control=False)
    background.interaction = False
    register_widget("background_map", background)


    @output
    @render.ui
    def main_ui():
        if game_state.get() == "start":
            return [
                output_widget("background_map"),
                ui.div(
                    {"class": "center-box"},
                    ui.h2("🎯 CH GeoGuess"),
                    ui.input_text("name_input", "Dein Name", placeholder="Gib deinen Namen ein..."),
                    ui.input_action_button("start_btn", "Start", class_="btn btn-primary mt-3"),
                )
            ]
        elif game_state.get() == "end":
              return []
        else:
            return [
                    ui.h3(f"Klicke auf: {random_gemeinde.get()['Gemeindename']}"),

                    output_widget("map_widget"),
                    ui.output_text("coord_text")
            ]

    @reactive.Effect
    @reactive.event(input.start_btn)
    def _():
        name = input.name_input().strip()
        if name:
            player_name.set(name)
            game_state.set("game")
            random_gemeinde.set(get_random_gemeinde())

    @reactive.Effect
    def setup_game():
        if not game_state.get() == "game":
            return

        esri_shaded = TileLayer(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
            attribution="Tiles © Esri — Source: Esri",
            max_zoom=13
        )

        m = Map(center=(46.8, 8.3), zoom=7, max_zoom=13)
        m.add_layer(esri_shaded)
        marker = Marker(location=(46.8, 8.3), draggable=True)
        m.add_layer(marker)

        def on_map_click(**kwargs):
            if kwargs.get("type") == "click":
                if count.get() <= 10:
                    latlng = kwargs.get("coordinates")
                    marker.location = latlng
                    clicked_coords.set((round(latlng[0], 5), round(latlng[1], 5)))
                    distance.set(distanz_berechnen_lv95(clicked_coords.get(), random_gemeinde.get()))
                    asyncio.create_task(lade_naechste_gemeinde())
                

        m.on_interaction(on_map_click)
        register_widget("map_widget", m)

    @output
    @render.text
    def coord_text():
        coords = clicked_coords.get()
        gemeinde = random_gemeinde.get()

    

        return (
            f"Distanz zur Lösung: {distance.get()} km"
        )

        return "Klicke auf die Karte, um deine Schätzung abzugeben."

# App starten
app = App(app_ui, server)