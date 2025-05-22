from shiny import App, ui, reactive, render
from shinywidgets import output_widget, register_widget
from ipyleaflet import Map, Marker

# Reaktive Variable
clicked_coords = reactive.Value(None)

# UI
app_ui = ui.page_fluid(
    ui.h3("🇨🇭 Klick auf Karte – Marker + Koordinaten"),
    output_widget("map_widget"),
    ui.output_text("coord_text")
)

# Server
def server(input, output, session):
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
# App
app = App(app_ui, server)
