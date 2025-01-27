# layouts.py
import dash_bootstrap_components as dbc
from dash import html, dcc
from dvr_iframe import dvr_html_content
from utils import build_records_table  # Si quieres usar algo de utils aquí
from dash_extensions import WebSocket

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
delete_modal = dbc.Modal(
    [
        dbc.ModalHeader("Confirmar eliminación"),
        dbc.ModalBody("¿Estás seguro de que deseas eliminar esta persona?"),
        dbc.ModalFooter(
            [
                dbc.Button("Cancelar", id="btn-cancel-delete", className="ml-auto", n_clicks=0),
                dbc.Button("Confirmar", id="btn-confirm-delete", color="danger", n_clicks=0)
            ]
        ),
    ],
    id="delete-confirm-modal",
    is_open=False,
)

delete_controls = html.Div([
    html.Div(id="delete-message"),
    dcc.Input(id="delete-persona-id", type="hidden"),
])
# Layout principal (app)
app_layout = dbc.Container(
    [
        html.H1("App Deteccion", style={'textAlign': 'center', 'color': 'white', 'marginTop': '20px'}),
        WebSocket(id="ws", url="ws://localhost:8000/ws/events"),
        dcc.Store(id="alerts-store", data=[]),  # Almacena alertas recientes en la sesión
        html.Div(id="alert-container", style={
            "position": "fixed",
            "top": "20px",
            "right": "20px",
            "width": "400px",
            "zIndex": 9999,
            "display": "flex",
            "flexDirection": "column-reverse"  # Asegura que las nuevas alertas se agreguen abajo
        }),
        dcc.Store(id='records-store', data=[]),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Tabs(
                        [
                            dbc.Tab(label="Registros", tab_id="registros"),
                            dbc.Tab(label="Cámaras", tab_id="camaras"),
                            dbc.Tab(label="Estadísticas", tab_id="estadisticas"), 
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
        # Store para manejar actualizaciones
        dcc.Store(id='users-update-store', data=0),
        html.Div(id='dummy-output', style={'display': 'none'}),
        delete_modal,
        delete_controls
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
            "Ver Actividad Reciente",
            id="open-activity-modal",
            color="info",
            style={'fontSize': '18px', 'margin': 'auto', 'display': 'block', 'marginTop': '20px'}
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Registro de Actividad Reciente", style={'fontSize': '24px'}),
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

delete_modal = dbc.Modal(
    [
        dbc.ModalHeader("Confirmar eliminación"),
        dbc.ModalBody("¿Estás seguro de que deseas eliminar esta persona?"),
        dbc.ModalFooter(
            [
                dbc.Button("Cancelar", id="btn-cancel-delete", className="ml-auto", n_clicks=0),
                dbc.Button("Confirmar", id="btn-confirm-delete", color="danger", n_clicks=0)
            ]
        ),
    ],
    id="delete-confirm-modal",
    is_open=False,
)

delete_controls = html.Div([
    html.Div(id="delete-message"),
    dcc.Input(id="delete-persona-id", type="hidden"),
])


estadisticas_layout = html.Div(
    style={'padding': '20px', 'backgroundColor': '#f9f9f9'},
    children=[
        html.H4(
            "Estadísticas Generales",
            style={'color': '#333', 'textAlign': 'center', 'fontSize': '24px', 'marginBottom': '20px'}
        ),
        dbc.Button(
            "Refrescar",
            id="btn-refrescar",
            color="primary",
            style={'marginBottom': '20px', 'display': 'block', 'margin': '0 auto'}
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H5("Detecciones de Poses", style={'textAlign': 'center', 'color': '#555'}),
                        dcc.Graph(id="grafico-1", style={'height': '400px', 'marginBottom': '40px'}),
                    ],
                    style={'marginBottom': '40px'}
                ),
                html.Div(
                    [
                        html.H5("Detecciones de Objetos", style={'textAlign': 'center', 'color': '#555'}),
                        dcc.Graph(id="grafico-2", style={'height': '400px', 'marginBottom': '40px'}),
                    ],
                    style={'marginBottom': '40px'}
                ),
                html.Div(
                    [
                        html.H5("Detecciones de Rostros", style={'textAlign': 'center', 'color': '#555'}),
                        dcc.Graph(id="grafico-3", style={'height': '400px'}),
                    ],
                ),
            ]
        ),
    ]
)