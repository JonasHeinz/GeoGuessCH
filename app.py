from shiny import App, ui, reactive, render
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, Marker
from utils.helpers import get_random_gemeinde

# Reaktive Zustände
player_name = reactive.Value("")
clicked_coords = reactive.Value(None)
game_started = reactive.Value(False)
random_gemeinde = reactive.Value(None)

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

    # Hintergrundkarte (Startbildschirm, ohne Interaktion)
    background = Map(center=(46.8, 8.3), zoom=7, scroll_wheel_zoom=False, zoom_control=False)
    background.interaction = False
    register_widget("background_map", background)

    # Dynamisches UI
    @output
    @render.ui
    def main_ui():
        if not game_started.get():
            # Startseite
            return [
                output_widget("background_map"),
                ui.div(
                    {"class": "center-box"},
                    ui.h2("🎯 CH GeoGuess"),
                    ui.input_text("name_input", "Dein Name", placeholder="Gib deinen Namen ein..."),
                    ui.input_action_button("start_btn", "Start", class_="btn btn-primary mt-3"),
                    ui.output_text("greeting_text")
                )
            ]
        else:
            # Spielansicht
            return [
                ui.h3(f"Viel Glück, {player_name.get()}!"),
                output_widget("map_widget"),
                ui.output_text("coord_text")
            ]

    # Beim Klick auf Start
    @reactive.Effect
    @reactive.event(input.start_btn)
    def _():
        name = input.name_input().strip()
        if name:
            player_name.set(name)
            game_started.set(True)
            random_gemeinde.set(get_random_gemeinde())

    @output
    @render.text
    def greeting_text():
        name = player_name.get()
        if name:
            return f"👋 Hallo {name}! Viel Spass mit CH GeoGuess!"
        return ""

    # Initialisierung des Spiels nach Start
    @reactive.Effect
    def setup_game():
        if not game_started.get():
            return

        m = Map(center=(46.8, 8.3), zoom=7)
        marker = Marker(location=(46.8, 8.3), draggable=True)
        m.add_layer(marker)

        def on_map_click(**kwargs):
            if kwargs.get("type") == "click":
                latlng = kwargs.get("coordinates")
                marker.location = latlng
                clicked_coords.set((round(latlng[0], 5), round(latlng[1], 5)))

        m.on_interaction(on_map_click)
        register_widget("map_widget", m)

    @output
    @render.text
    def coord_text():
        coords = clicked_coords.get()
        if coords:
            return f"📍 Koordinaten: {coords[0]}, {coords[1]}"
        return "Klicke auf die Karte."

# App starten
app = App(app_ui, server)

