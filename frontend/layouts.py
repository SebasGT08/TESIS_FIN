# layouts.py
import dash_bootstrap_components as dbc
from dash import html, dcc
from dvr_iframe import dvr_html_content
from utils import build_records_table  # Si quieres usar algo de utils aquí
# Layout de Login
login_layout = dbc.Container(
    [
        html.Div(
            [
                html.H1("Inicio de Sesión", style={'textAlign': 'center', 'color': 'white'}),
                dbc.Input(id="login-usuario", placeholder="Usuario", type="text", style={'marginBottom': '10px'}),
                dbc.Input(id="login-password", placeholder="Contraseña", type="password", style={'marginBottom': '10px'}),
                dbc.Button("Iniciar Sesión", id="btn-login", color="primary", style={'width': '100%'}),
                html.Div(id="login-feedback", style={'marginTop': '10px', 'textAlign': 'center', 'color': 'red'}),
            ],
            style={
                'width': '300px',
                'margin': 'auto',
                'backgroundColor': '#2C2C2C',
                'padding': '20px',
                'borderRadius': '5px',
                'boxShadow': '0px 0px 10px #000'
            }
        )
    ],
    fluid=True,
    style={'height': '100vh', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
)

# Layout principal (app)
app_layout = dbc.Container(
    [
        html.H1("Registro Facial", style={'textAlign': 'center', 'color': 'white', 'marginTop': '20px'}),
       html.Div(id="alert-container", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "width": "400px",
            "zIndex": 9999,
            "display": "flex",
            "flexDirection": "column-reverse"  # Asegura que las nuevas alertas se agreguen abajo
        }),
        dcc.Interval(id="interval", interval=5000, n_intervals=0),

        dbc.Row(
            [
                dbc.Col(
                    dbc.Tabs(
                        [
                            dbc.Tab(label="Registros", tab_id="registros"),
                            dbc.Tab(label="Cámaras", tab_id="camaras"),
                        ],
                        id="tabs",
                        active_tab="registros",
                        style={'marginBottom': '0px'}
                    ),
                    width=9
                ),
                dbc.Col(
                    dbc.Button("Salir", id="logout-button", color="danger", style={'float': 'right'}),
                    width=3,
                    style={'textAlign': 'right'}
                ),
            ],
            align="center",
            justify="between",
            style={'marginBottom': '20px'}
        ),
        # Contenedor donde se mostrará el contenido de cada Tab
        html.Div(
            id="tab-content",
            style={'backgroundColor': '#2C2C2C', 'height': '100%'}
        ),
        # Intervalo para refrescar datos
        dcc.Interval(id="interval", interval=2000),
        dcc.Store(id='users-update-store', data=0),
        html.Div(id='dummy-output', style={'display': 'none'}),
    ],
    fluid=True,
    style={'backgroundColor': '#2C2C2C', 'height': '100vh', 'padding': '20px'}
)

# Layout global para manejar la navegación
layout_with_url = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),   # Para manejar la ruta actual
        html.Div(id="page-content")              # Muestra login o app
    ],
    fluid=True,
    style={'backgroundColor': '#2C2C2C', 'height': '100vh'}
)


# Opcional: Crear un layout de Cámaras que use el Iframe
camaras_layout = html.Div(
    style={'padding': '20px'},
    children=[
        html.H4(
            "Stream de Cámaras - DVR View",
            style={'color': 'white', 'textAlign': 'center', 'fontSize': '24px'}
        ),
        html.Iframe(
            srcDoc=dvr_html_content,
            style={"width": "100%", "height": "70vh", "border": "none"},
        ),
        dbc.Button(
            "Ver Actividad",
            id="open-activity-modal",
            color="info",
            style={'fontSize': '18px', 'margin': 'auto', 'display': 'block', 'marginTop': '20px'}
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Registro de Actividad", style={'fontSize': '24px'}),
                    close_button=True
                ),
                dbc.ModalBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    id="modal-activity-logs",
                                    style={
                                        'backgroundColor': '#3A3A3A',
                                        'padding': '10px',
                                        'borderRadius': '5px'
                                    }
                                ),
                                width=6
                            ),
                            dbc.Col(
                                dcc.Graph(
                                    id="modal-activity-graph",
                                    style={'height': '400px'}
                                ),
                                width=6
                            )
                        ]
                    )
                ),
            ],
            id="activity-modal",
            is_open=False,
            size="xl",
            backdrop=True,
            scrollable=True
        ),
    ]
)

