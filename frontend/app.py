# app.py
import dash
import dash_bootstrap_components as dbc
from layouts import layout_with_url  # Importa tu layout global

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)
app.title = 'Registro Facial'
server = app.server

# Asigna el layout global a la app
app.layout = layout_with_url
