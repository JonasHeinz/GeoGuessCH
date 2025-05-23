from shiny import App, ui, reactive, render
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, Marker, TileLayer, Icon, Polyline
from utils.helpers import vorbereite_spiel_runden, get_next_gemeinde, distanz_berechnen_lv95, lv95_to_wgs84, lade_gemeinden
import asyncio
import json
from ipyleaflet import GeoJSON
import geopandas as gpd

# UI
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.script("""
    function toggleRules() {
        var x = document.getElementById("rules-box");
        if (x.style.display === "none") {
            x.style.display = "block";
        } else {
            x.style.display = "none";
}
}
"""),
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
            .top-right-box {
            position: fixed;
            top: 10px;
            right: 20px;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px 15px;
            border-radius: 8px;
            box-shadow: 0px 0px 10px rgba(0,0,0,0.2);
            font-size: 18px;
            z-index: 1000;
}
            """
        )
    ),
    output_widget("background_map"),

    ui.output_ui("main_ui")
)

# Reaktive Zustände
player_name = reactive.Value("")
clicked_coords = reactive.Value(None)
game_state = reactive.Value("start")
random_gemeinde = reactive.Value(None)
count = reactive.Value(0)
total_distance = reactive.Value(0)
distance = reactive.Value(0)
map_widget = reactive.Value(None)
countdown = reactive.Value(0)
click_enabled = reactive.Value(True)

async def lade_naechste_gemeinde():
    click_enabled.set(False)
    game_state.set("between")  # <== Neu: Zwischenanzeige
    countdown.set(3)
    for i in range(3, 0, -1):
        countdown.set(i)
    countdown.set(0)
    random_gemeinde.set(get_next_gemeinde())
    clicked_coords.set(None)
    click_enabled.set(True)
    
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
                    ui.input_text("name_input", "",
                                  placeholder="Gib deinen Namen ein..."),
                    ui.input_action_button(
                        "start_btn", "Start", class_="btn btn-primary mt-3"),
                    ui.tags.button("Spielregeln", {
                                   "onclick": "toggleRules()", "class": "btn btn-link mt-3 ms-3"}),
                    ui.div(
                        {"id": "rules-box",
                            "style": "display: none; margin-top: 20px; text-align: left;"},
                        ui.h4("Spielregeln"),
                        ui.p(
                            "Ein Spiel dauert 10 Runden, in denen du 10 verschiedene Ortschaften auf der Karte anklicken musst."),
                        ui.p(
                            "Die maximale Punktzahl pro Runde sind 100 Punkte. Pro Kilometer Abweichung wird 1 Punkt abgezogen."),
                        ui.p("Beispiel: 2 km daneben = 98 Punkte."),
                        ui.p(
                            "Am Ende werden alle Punkte summiert. Die Zeit spielt keine Rolle.")
                    )
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
                    ui.input_action_button(
                        "end_btn", "Spiel beenden", class_="btn btn-primary mt-3"),
                )
            ]
        elif game_state.get() == "between":
            return [
                ui.div(
                    {
                        "style": """
                            position: fixed;
                            top: 10px;
                            left: 50%;
                            transform: translateX(-50%);
                            background-color: rgba(255, 255, 255, 0.95);
                            padding: 20px;
                            border-radius: 12px;
                            box-shadow: 0px 0px 10px rgba(0,0,0,0.3);
                            z-index: 999;
                            text-align: center;
                            min-width: 280px;
                        """
                    },
                    ui.h4(f"Distanz zur letzten Gemeinde: {distance.get():.2f} km"),
                    ui.h5(ui.output_text("countdown_timer"))
                ),
                output_widget("map_widget")  # <== Karte hier einblenden
            ]
              
        elif game_state.get() == "game":
            return [
                ui.div({"class": "top-right-box"}),
                ui.h3(f"Suche Ort: {random_gemeinde.get()['Gemeindename']}"),
                output_widget("map_widget"),
                ui.output_text("coord_text"),
            ]

      



    @reactive.Effect
    @reactive.event(input.weiter_btn)
    def weiter_btn():
            game_state.set("game")  # <== zurück in Spielrunde
            
    @reactive.Effect
    @reactive.event(input.start_btn)
    def start_game():
        name = input.name_input().strip()
        if name:
            player_name.set(name)
            vorbereite_spiel_runden(10)  # Hier vorbereiten
            game_state.set("game")
            random_gemeinde.set(get_next_gemeinde())
            count.set(0)
            total_distance.set(0)
            distance.set(0)
            clicked_coords.set(None)
            map_widget.set(None)

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
        ziel_marker = Marker(location=(0, 0), icon=red_icon,
                             draggable=False, opacity=0.9)

        marker = Marker(location=(46.8, 8.3), draggable=True)
        m.add_layer(marker)

        linie = Polyline(locations=[], color="red", weight=4)
        m.add_layer(linie)

        def on_map_click(**kwargs):
            if not click_enabled.get():
                return 
            if kwargs.get("type") == "click":
                if count.get() < 5:  # Beispiel: max 5 Versuche
                    latlng = kwargs.get("coordinates")
                    if not latlng or not random_gemeinde.get():
                        return

                    marker.location = latlng
                    clicked_coords.set(
                        (round(latlng[0], 5), round(latlng[1], 5)))

                    # Berechnung der Distanz
                    distanz = distanz_berechnen_lv95(
                        clicked_coords.get(), random_gemeinde.get())
                    distance.set(distanz)
                    total_distance.set(total_distance.get() + distanz)

                    ziel_e = float(random_gemeinde.get()["E"])
                    ziel_n = float(random_gemeinde.get()["N"])
                    ziel_lat, ziel_lon = lv95_to_wgs84(ziel_e, ziel_n)

                    ziel_marker.location = (ziel_lat, ziel_lon)
                    if ziel_marker not in m.layers:
                        m.add_layer(ziel_marker)

                    linie.locations = [marker.location, ziel_marker.location]

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
    def countdown_timer():
        if countdown.get() > 0:
            return f"Nächste Gemeinde in {countdown.get()}s"
        return ""
    @output
    @render.text
    def coord_text():
        if not clicked_coords.get():
            return "Klicke auf die Karte, um deine Schätzung abzugeben."
        return f"Distanz zur Lösung: {distance.get():.2f} km"


# App starten
app = App(app_ui, server)
