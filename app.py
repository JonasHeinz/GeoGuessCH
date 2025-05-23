from shiny import App, ui, reactive, render
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, Marker, TileLayer, Icon, Polyline, GeoJSON
from utils.helpers import vorbereite_spiel_runden, get_next_gemeinde, distanz_berechnen_lv95, lv95_to_wgs84
from leaderboard import lade_leaderboard, schreibe_leaderboard
import json

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
        ui.tags.style("""
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
            .leaflet-interactive {
                pointer-events: none !important;
            }
           .btn {
            background-color: green;
            color: white;
            padding: 10px 15px;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }

        .btn:hover {
            background-color: black;
        }
        """)
    ),
    output_widget("background_map"),
    ui.output_ui("main_ui")
)

# Reaktive Zustände
player_name = reactive.Value("")
spielmodus = reactive.Value("Ortschaften")
clicked_coords = reactive.Value(None)
game_state = reactive.Value("home")
random_gemeinde = reactive.Value(None)
count = reactive.Value(0)
total_distance = reactive.Value(0)
distance = reactive.Value(0)
map_widget = reactive.Value(None)
click_enabled = reactive.Value(True)
warte_auf_letzten_klick = reactive.Value(False)

def server(input, output, session):
    background = Map(center=(46.8, 8.3), zoom=7,
                     scroll_wheel_zoom=False, zoom_control=False)
    background.interaction = False
    register_widget("background_map", background)

    @output
    @render.ui
    def main_ui():
        if game_state.get() == "home":
            return [
                ui.div(
                    {"class": "center-box"},
                    ui.h1("Willkommen zu Swiss GeoGuess"),
                    ui.p("Entdecke Schweizer Gemeinden, Berge, Hütten oder Pässe – wie gut kennst du dein Land?"),
                    ui.input_text("name_input", "", placeholder="Gib deinen Namen ein..."),
                    ui.input_select("spielmodus", "Was möchtest du spielen?", choices=[
                        "Ortschaften",
                        "2000er-Berge",
                        "3000er-Berge",
                        "4000er-Berge",
                        "Berghütten",
                        "Passstrassen"
                    ], selected="Ortschaften"),
                    ui.input_action_button("weiter_btn", "Spiel starten", class_="btn btn-success mt-4")
                )
            ]

        elif game_state.get() == "start":
            return [
                ui.div(
                    {"class": "center-box"},
                    ui.h2("Swiss GeoGuess"),
                    ui.input_action_button("start_btn", "Neue Runde", class_="btn btn-primary mt-3"),
                    ui.input_action_button("startseite_btn", "Startseite", class_="btn btn-secondary mt-3"),
                    ui.tags.button("Spielregeln", {"onclick": "toggleRules()", "class": "btn btn-link mt-3 ms-3"}),
                    ui.div(
                        {"id": "rules-box", "style": "display: none; margin-top: 20px; text-align: left;"},
                        ui.h4("Spielregeln"),
                        ui.p("Ein Spiel dauert 5 Runden. Du musst auf der Karte den gesuchten Ort anklicken."),
                        ui.p("Der blaue Marker ist dein Tipp, der rote Marker zeigt den gesuchten Ort."),
                        ui.p("Am Ende wird die Gesamtdistanz in km berechnet.")
                    )
                )
            ]

        elif game_state.get() == "end":
            schreibe_leaderboard(player_name.get(), total_distance.get(), spielmodus.get())
            top10 = lade_leaderboard(spielmodus.get())
            return [
                ui.div(
                    {"class": "center-box"},
                    ui.h3("Swiss GeoGuess"),
                    ui.h4(f"Gut gemacht, {player_name.get()}!"),
                    ui.h5("Spiel beendet."),
                    ui.h4("Gesamtdistanz:"),
                    ui.output_text("total_distance_text"),
                    ui.h4("Top 10 Leaderboard"),
                    ui.tags.ul([ui.tags.li(f"{i+1}. {e['Name']}: {float(e['Kilometer']):.2f} km") for i, e in enumerate(top10)]),
                    ui.input_action_button("end_btn", "Zurück", class_="btn btn-primary mt-3")
                )
            ]

        elif game_state.get() == "game":
            content = [
                ui.h3(f"Finde: {random_gemeinde.get()['NAME']}")
            ]
            if distance.get() > 0:
                content.append(
                    ui.div(
                        {
                            "style": """
                                position: fixed;
                                top: 10px;
                                left: 50%;
                                transform: translateX(-50%);
                                background-color: rgba(255, 255, 255, 0.95);
                                padding: 15px 20px;
                                border-radius: 12px;
                                box-shadow: 0px 0px 10px rgba(0,0,0,0.2);
                                z-index: 999;
                                text-align: center;
                            """
                        },
                        ui.h5(ui.output_text("distanz_anzeige"))
                    )
                )
            content.extend([
                output_widget("map_widget"),
                ui.output_text("coord_text")
            ])
            return content

    @reactive.Effect
    @reactive.event(input.weiter_btn)
    def set_player_and_mode():
        name = input.name_input().strip()
        if name:
            player_name.set(name)
            spielmodus.set(input.spielmodus())
            game_state.set("start")

    @reactive.Effect
    @reactive.event(input.start_btn)
    def start_game():
        modus_map = {
            "Ortschaften": "Ortschaften.csv",
            "Berge ab 2000m": "Berge2000.csv",
            "Berge ab 3000m": "Berge3000.csv",
            "4000er-Berge": "Berge4000.csv",
            "Berghütten": "Berghuetten.csv",
            "Passstrassen": "Passstrassen.csv"
        }
        dateiname = modus_map.get(spielmodus.get(), "Ortschaften.csv")
        vorbereite_spiel_runden(6, datei=dateiname)
        game_state.set("game")
        random_gemeinde.set(get_next_gemeinde())
        count.set(0)
        total_distance.set(0)
        distance.set(0)
        clicked_coords.set(None)
        map_widget.set(None)
        click_enabled.set(True)
        warte_auf_letzten_klick.set(False)

    @reactive.Effect
    @reactive.event(input.startseite_btn)
    def gehe_zur_startseite():
        game_state.set("home")
        player_name.set("")
        random_gemeinde.set(None)
        count.set(0)
        total_distance.set(0)
        distance.set(0)
        clicked_coords.set(None)
        map_widget.set(None)

    @reactive.Effect
    @reactive.event(input.end_btn)
    def reset_game():
        game_state.set("start")
        random_gemeinde.set(None)
        count.set(0)
        total_distance.set(0)
        distance.set(0)
        clicked_coords.set(None)
        map_widget.set(None)

    @reactive.Effect
    def setup_game():
        if game_state.get() != "game" or map_widget.get() is not None:
            return

        with open("data/kantonsgrenzen_2d.geojson", "r", encoding="utf-8") as f:
            data = json.load(f)

        kantonsgrenzen = GeoJSON(data=data, name="Kantonsgrenzen",
                                 interactive=False,
                                 style={"color": "white", "weight": 0.5, "fillOpacity": 0.0})

        esri_shaded = TileLayer(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png"
        )

        m = Map(center=(46.8, 8.3), zoom=7, min_zoom=7, max_zoom=13,
                scroll_wheel_zoom=True, max_bounds=[[45.5, 5.5], [47.9, 10.5]],
                layout={"height": "80vh"})

        m.add_layer(kantonsgrenzen)
        m.add_layer(esri_shaded)

        marker = Marker(location=(46.8, 8.3), draggable=True)
        red_icon = Icon(icon_url="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
                        icon_size=[25, 41], icon_anchor=[12, 41])
        ziel_marker = Marker(location=(0, 0), icon=red_icon, draggable=False)
        linie = Polyline(locations=[], color="red", weight=4)
        m.add_layer(linie)

        def on_map_click(**kwargs):
            if kwargs.get("type") != "click":
                return

            if warte_auf_letzten_klick.get():
                warte_auf_letzten_klick.set(False)
                game_state.set("end")
                return

            if not click_enabled.get() or not random_gemeinde.get():
                return

            latlng = kwargs.get("coordinates")
            if not latlng:
                return

            if marker not in m.layers:
                m.add_layer(marker)

            marker.location = latlng
            clicked_coords.set((round(latlng[0], 5), round(latlng[1], 5)))

            distanz = distanz_berechnen_lv95(clicked_coords.get(), random_gemeinde.get())
            distance.set(distanz)
            total_distance.set(total_distance.get() + distanz)

            ziel_lat, ziel_lon = lv95_to_wgs84(float(random_gemeinde.get()["E"]), float(random_gemeinde.get()["N"]))
            ziel_marker.location = (ziel_lat, ziel_lon)
            if ziel_marker not in m.layers:
                m.add_layer(ziel_marker)

            linie.locations = [marker.location, ziel_marker.location]

            if count.get() < 4:
                count.set(count.get() + 1)
                random_gemeinde.set(get_next_gemeinde())
                clicked_coords.set(None)
            else:
                click_enabled.set(False)
                warte_auf_letzten_klick.set(True)

        m.on_interaction(on_map_click)
        register_widget("map_widget", m)
        map_widget.set(m)

    @output
    @render.text
    def coord_text():
        if not clicked_coords.get():
            return "Klicke auf die Karte, um deinen Tipp abzugeben."
        return f"Distanz zur Lösung: {distance.get():.2f} km"

    @output
    @render.text
    def total_distance_text():
        return f"{total_distance.get():.2f} km"

    @output
    @render.text
    def distanz_anzeige():
        return f"Distanz zur Lösung: {distance.get():.2f} km"

app = App(app_ui, server)
