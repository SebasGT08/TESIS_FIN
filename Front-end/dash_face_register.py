import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import socketio
import requests
import plotly.graph_objects as go

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
app.title = 'Registro Facial'

sio = socketio.Client()

latest_frame = None
activity_logs_facial = []
activity_logs_objetos = []
activity_logs_poses = []
detection_count_facial = 0
detection_count_objetos = 0
detection_count_poses = 0

# --------------------------------------------------------------------------------------
# Evento de Socket.IO para simular recepción de frames y contadores de actividad
# --------------------------------------------------------------------------------------
@sio.on('video_frame')
def handle_video_frame(data):
    global latest_frame
    global detection_count_facial, detection_count_objetos, detection_count_poses
    global activity_logs_facial, activity_logs_objetos, activity_logs_poses

    # Recibimos el frame (base64) y actualizamos contadores
    latest_frame = data['frame']

    # Simulación de detecciones
    detection_count_facial += 1
    detection_count_objetos += 1
    detection_count_poses += 1

    activity_logs_facial.append(f"Detección Facial #{detection_count_facial}")
    activity_logs_objetos.append(f"Detección de Objetos #{detection_count_objetos}")
    activity_logs_poses.append(f"Detección de Poses #{detection_count_poses}")

# Conexión Socket.IO (ajusta la URL a tu backend real)
sio.connect('http://127.0.0.1:5000')

# --------------------------------------------------------------------------------------
# Función auxiliar para construir la tabla de registros
# --------------------------------------------------------------------------------------
def build_records_table():
    """
    Llama al endpoint /get_records del backend,
    crea y retorna la tabla con los datos.
    """
    try:
        response = requests.get("http://127.0.0.1:5000/get_records")
        if response.status_code == 200:
            records = response.json()
            if not records:
                return html.Div(
                    "No hay registros disponibles.",
                    style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
                )

            table_header = [
                html.Thead(
                    html.Tr([
                        html.Th("ID", style={'width': '20%', 'fontSize': '18px'}),
                        html.Th("Persona", style={'width': '40%', 'fontSize': '18px'}),
                        html.Th("Fecha", style={'width': '40%', 'fontSize': '18px'})
                    ])
                )
            ]
            table_body = html.Tbody([
                html.Tr([
                    html.Td(record["id"], style={'fontSize': '16px'}),
                    html.Td(record["persona"], style={'fontSize': '16px'}),
                    html.Td(record["fecha"], style={'fontSize': '16px'}),
                ]) for record in records
            ])

            return dbc.Table(
                table_header + [table_body],
                bordered=True,
                dark=True,
                hover=True,
                responsive=True,
                striped=True,
                style={
                    'color': 'white',
                    'backgroundColor': '#2C2C2C',
                    'fontSize': '18px',
                    'width': '80%',
                    'margin': '0 auto'
                }
            )
        else:
            return html.Div(
                "Error al obtener registros.",
                style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
            )
    except Exception as e:
        return html.Div(
            f"Error de conexión: {e}",
            style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
        )


# --------------------------------------------------------------------------------------
# Layout principal
# --------------------------------------------------------------------------------------
app.layout = dbc.Container(
    [
        html.H1("Registro Facial", style={'textAlign': 'center', 'color': 'white', 'marginTop': '20px'}),

        dbc.Tabs(
            [
                dbc.Tab(label="Registros", tab_id="registros"),
                dbc.Tab(label="Cámaras", tab_id="camaras"),
            ],
            id="tabs",
            active_tab="registros",
            style={'marginBottom': '20px'}
        ),
        # Contenido dinámico de cada pestaña
        html.Div(id="tab-content", style={'backgroundColor': '#2C2C2C', 'height': '100%'}),

        # Intervalo para refrescar datos (cámaras, actividad)
        dcc.Interval(id="interval", interval=2000)
    ],
    fluid=True,
    style={'backgroundColor': '#2C2C2C', 'height': '100vh', 'padding': '20px'}
)


# --------------------------------------------------------------------------------------
# Callback para renderizar el contenido de cada Tab
# --------------------------------------------------------------------------------------
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "registros":
        # Construimos la tabla de registros *desde el inicio*
        records_table = build_records_table()

        return html.Div(
            style={'padding': '20px'},
            children=[
                dbc.Row(
                    [
                        # Columna con el Upload y la imagen
                        dbc.Col(
                            [
                                dcc.Upload(
                                    id='upload-image',
                                    children=html.Div([
                                        'Arrastra y suelta o ',
                                        html.A('Selecciona una Imagen', style={'color': '#2CA8FF', 'fontSize': '18px'})
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '80px',
                                        'lineHeight': '80px',
                                        'borderWidth': '2px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        'margin': '10px',
                                        'color': 'white',
                                        'fontSize': '18px'
                                    },
                                    multiple=False
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "Imagen Cargada",
                                            style={
                                                'color': 'white',
                                                'backgroundColor': '#1C1C1C',
                                                'fontSize': '20px'
                                            }
                                        ),
                                        dbc.CardBody(
                                            html.Div(
                                                id='original-image',
                                                style={
                                                    'width': '100%',
                                                    'height': '350px',
                                                    'display': 'flex',
                                                    'justifyContent': 'center',
                                                    'alignItems': 'center',
                                                    'overflow': 'hidden'
                                                }
                                            ),
                                            style={'backgroundColor': '#2C2C2C'}
                                        ),
                                    ],
                                    style={
                                        'margin': '10px',
                                        'backgroundColor': '#2C2C2C',
                                        'border': '2px solid #444'
                                    }
                                ),
                            ],
                            width=6
                        ),
                        # Columna con el registro de persona
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(
                                            "Registro de Persona",
                                            style={
                                                'color': 'white',
                                                'backgroundColor': '#1C1C1C',
                                                'fontSize': '20px'
                                            }
                                        ),
                                        dbc.CardBody(
                                            [
                                                dbc.Input(
                                                    id="input-name",
                                                    placeholder="Ingresa tu nombre",
                                                    type="text",
                                                    style={
                                                        'marginBottom': '20px',
                                                        'fontSize': '18px',
                                                        'width': '70%',
                                                        'height': '45px'
                                                    }
                                                ),
                                                dbc.Button(
                                                    "Guardar",
                                                    id="save-button",
                                                    color="primary",
                                                    size="lg",
                                                    style={
                                                        'marginBottom': '10px',
                                                        'fontSize': '18px',
                                                        'width': '70%',
                                                        'height': '50px'
                                                    }
                                                ),
                                                html.Div(
                                                    id='output-message',
                                                    style={'marginTop': '10px', 'fontSize': '16px'}
                                                )
                                            ],
                                            style={'backgroundColor': '#2C2C2C'}
                                        ),
                                    ],
                                    style={
                                        'margin': '10px',
                                        'backgroundColor': '#2C2C2C',
                                        'border': '2px solid #444'
                                    }
                                ),
                            ],
                            width=6
                        ),
                    ]
                ),
                html.Hr(),
                html.H4(
                    "Lista de Registros",
                    style={
                        'color': 'white',
                        'textAlign': 'center',
                        'marginTop': '20px',
                        'fontSize': '24px'
                    }
                ),
                html.Div(
                    id="records-table",
                    children=records_table,  # Mostramos la tabla desde el inicio
                    style={'margin': '20px', 'textAlign': 'center'}
                )
            ]
        )

    elif active_tab == "camaras":
        # Dividimos las cámaras en 4 secciones (2 filas x 2 columnas)
        return html.Div(
            style={'padding': '20px'},
            children=[
                html.H4("Stream de Cámaras", style={'color': 'white', 'textAlign': 'center', 'fontSize': '24px'}),
                
                # Fila 1: 2 cámaras
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Cámara 1 - Recon. Facial", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Img(
                                        id="video-feed-1",
                                        style={
                                            'width': '100%',
                                            'height': '300px',
                                            'border': '2px solid white'
                                        }
                                    ),
                                ],
                                style={
                                    'display': 'flex',
                                    'flexDirection': 'column',
                                    'alignItems': 'center',
                                    'justifyContent': 'center',
                                    'backgroundColor': '#2C2C2C',
                                    'borderRadius': '10px',
                                    'overflow': 'hidden',
                                    'marginBottom': '20px'
                                }
                            ),
                            width=6
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Cámara 2 - YOLO (Objetos)", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Canvas(
                                        id="videoCanvas",
                                        style={
                                            'width': '100%',
                                            'height': '300px',
                                            'border': '2px solid white'
                                        }
                                    ),
                                ],
                                style={
                                    'display': 'flex',
                                    'flexDirection': 'column',
                                    'alignItems': 'center',
                                    'justifyContent': 'center',
                                    'backgroundColor': '#2C2C2C',
                                    'borderRadius': '10px',
                                    'overflow': 'hidden',
                                    'marginBottom': '20px'
                                }
                            ),
                            width=6
                        ),
                    ]
                ),

                # Fila 2: 2 cámaras
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Cámara 3 - Recon. de Poses", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Img(
                                        id="video-feed-3",
                                        style={
                                            'width': '100%',
                                            'height': '300px',
                                            'border': '2px solid white'
                                        }
                                    ),
                                ],
                                style={
                                    'display': 'flex',
                                    'flexDirection': 'column',
                                    'alignItems': 'center',
                                    'justifyContent': 'center',
                                    'backgroundColor': '#2C2C2C',
                                    'borderRadius': '10px',
                                    'overflow': 'hidden'
                                }
                            ),
                            width=6
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Cámara 4 - Adicional", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Img(
                                        id="video-feed-4",
                                        style={
                                            'width': '100%',
                                            'height': '300px',
                                            'border': '2px solid white'
                                        }
                                    ),
                                ],
                                style={
                                    'display': 'flex',
                                    'flexDirection': 'column',
                                    'alignItems': 'center',
                                    'justifyContent': 'center',
                                    'backgroundColor': '#2C2C2C',
                                    'borderRadius': '10px',
                                    'overflow': 'hidden'
                                }
                            ),
                            width=6
                        ),
                    ]
                ),

                # Botón para abrir el modal de actividad
                dbc.Button(
                    "Ver Actividad",
                    id="open-activity-modal",
                    color="info",
                    style={'fontSize': '18px', 'margin': 'auto', 'display': 'block', 'marginTop': '20px'}
                ),

                # Modal con logs y gráfica (en 2 columnas)
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle("Registro de Actividad", style={'fontSize': '24px'}),
                            close_button=True  # la "X" para cerrar
                        ),
                        dbc.ModalBody(
                            dbc.Row(
                                [
                                    # Columna izquierda: logs de detecciones
                                    dbc.Col(
                                        html.Div(
                                            id="modal-activity-logs",
                                            style={
                                                'color': 'white',
                                                'backgroundColor': '#3A3A3A',
                                                'padding': '10px',
                                                'borderRadius': '5px',
                                                'maxHeight': '400px',
                                                'overflowY': 'auto'
                                            }
                                        ),
                                        width=6
                                    ),
                                    # Columna derecha: gráfica de conteo
                                    dbc.Col(
                                        dcc.Graph(
                                            id="modal-activity-graph",
                                            style={
                                                'height': '400px'
                                            }
                                        ),
                                        width=6
                                    )
                                ]
                            )
                        ),
                    ],
                    id="activity-modal",
                    is_open=False,  # Cerrado por defecto
                    size="xl",
                    backdrop=True,
                    scrollable=True
                ),
            ]
        )
    return "Seleccione una pestaña para ver el contenido."


# --------------------------------------------------------------------------------------
# Callback para mostrar el frame de las cámaras (4 salidas)
# --------------------------------------------------------------------------------------
@app.callback(
    [Output("video-feed-1", "src"),
     Output("videoCanvas", "children"),
     Output("video-feed-3", "src"),
     Output("video-feed-4", "src")],
    [Input("interval", "n_intervals"), Input("tabs", "active_tab")]
)
def update_frame(_, active_tab):
    if active_tab != "camaras":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    global latest_frame
    if latest_frame:
        src_value = f"data:image/jpeg;base64,{latest_frame}"
        # Ejemplo: si tienes solo 3 cámaras, la 4ta podría mostrar la misma imagen o quedar en dash.no_update
        # Para la demo, mostramos la misma imagen en la 4ta
        return src_value, None, src_value, src_value
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# --------------------------------------------------------------------------------------
# Callback para mostrar la imagen cargada en 'upload-image'
# --------------------------------------------------------------------------------------
@app.callback(
    Output('original-image', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename')
)
def display_images(content, filename):
    if content:
        image = html.Img(
            src=content,
            style={
                'maxWidth': '100%',
                'maxHeight': '100%',
                'objectFit': 'contain'
            }
        )
        return image
    return None


# --------------------------------------------------------------------------------------
# Callback para:
#  1) Enviar datos al backend (registro de persona).
#  2) Mostrar mensaje de éxito / error.
#  3) Limpiar campos (nombre e imagen).
#  4) Actualizar la tabla de registros automáticamente.
# --------------------------------------------------------------------------------------
@app.callback(
    [
        Output('output-message', 'children'),
        Output('input-name', 'value'),
        Output('upload-image', 'contents'),
        Output('records-table', 'children'),
    ],
    [Input('save-button', 'n_clicks')],
    [State('upload-image', 'contents'), State('input-name', 'value'), State('tabs', 'active_tab')]
)
def enviar_datos_backend(n_clicks, image_content, name, active_tab):
    # Solo actuamos si se hizo clic en "Guardar" y la pestaña activa es "registros"
    if active_tab != "registros" or not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Intentamos registrar
    if image_content and name:
        image_data = image_content.split(",")[1]
        payload = {
            'name': name,
            'image': image_data
        }
        try:
            response = requests.post('http://127.0.0.1:5000/register', json=payload)
            if response.status_code == 200:
                # Registro exitoso
                alert = dbc.Alert("Registro exitoso.", color="success", duration=3000)
                # Limpiamos los campos
                new_name = ""
                new_image = None
                # Construimos la tabla actualizada
                new_table = build_records_table()
                return alert, new_name, new_image, new_table
            else:
                error_msg = response.json().get('error', 'Error desconocido')
                alert = dbc.Alert(f"Error del backend: {error_msg}", color="danger")
                return alert, dash.no_update, dash.no_update, dash.no_update
        except Exception as e:
            alert = dbc.Alert(f"Error de conexión con el backend: {e}", color="danger")
            return alert, dash.no_update, dash.no_update, dash.no_update
    else:
        alert = dbc.Alert("Por favor, carga una imagen y escribe un nombre.", color="warning")
        return alert, dash.no_update, dash.no_update, dash.no_update


# --------------------------------------------------------------------------------------
# Callback para abrir/cerrar el Modal de Actividad
# --------------------------------------------------------------------------------------
@app.callback(
    Output("activity-modal", "is_open"),
    [Input("open-activity-modal", "n_clicks")],
    [State("activity-modal", "is_open")]
)
def toggle_activity_modal(n_clicks_open, is_open):
    # Clic en "Ver Actividad" alterna el estado del modal
    if n_clicks_open:
        return not is_open
    return is_open


# --------------------------------------------------------------------------------------
# Callback para actualizar logs y la gráfica dentro del Modal
# --------------------------------------------------------------------------------------
@app.callback(
    [Output("modal-activity-logs", "children"),
     Output("modal-activity-graph", "figure")],
    Input("interval", "n_intervals"),
    State("tabs", "active_tab")
)
def update_activity_logs(_, active_tab):
    """
    Se actualizarán los logs de detecciones y la gráfica
    periódicamente si estamos en la pestaña "cámaras".
    """
    if active_tab != "camaras":
        return dash.no_update, dash.no_update

    global activity_logs_facial, activity_logs_objetos, activity_logs_poses
    global detection_count_facial, detection_count_objetos, detection_count_poses

    # Unificamos los últimos 50 logs en una sola lista (ordenados por tipo).
    logs_combined = []

    if activity_logs_facial:
        logs_combined.append(html.Div("Detecciones Faciales:", style={'fontWeight': 'bold'}))
        logs_combined += [html.Div(log) for log in activity_logs_facial[-50:]]

    if activity_logs_objetos:
        logs_combined.append(html.Hr())
        logs_combined.append(html.Div("Detecciones de Objetos:", style={'fontWeight': 'bold'}))
        logs_combined += [html.Div(log) for log in activity_logs_objetos[-50:]]

    if activity_logs_poses:
        logs_combined.append(html.Hr())
        logs_combined.append(html.Div("Detecciones de Poses:", style={'fontWeight': 'bold'}))
        logs_combined += [html.Div(log) for log in activity_logs_poses[-50:]]

    # Gráfica de barras con conteo total
    x_values = ["Facial", "Objetos", "Poses"]
    y_values = [detection_count_facial, detection_count_objetos, detection_count_poses]

    fig = go.Figure(data=[go.Bar(x=x_values, y=y_values, marker_color=['#2ca02c', '#1f77b4', '#d62728'])])
    fig.update_layout(
        title="Conteo de Detecciones",
        xaxis_title="Tipo de Reconocimiento",
        yaxis_title="Conteo",
        template="plotly_dark",
        paper_bgcolor='#2C2C2C',
        plot_bgcolor='#2C2C2C',
        font_color='white'
    )

    return logs_combined, fig


# --------------------------------------------------------------------------------------
# Arranque de la app
# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
