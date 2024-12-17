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

@sio.on('video_frame')
def handle_video_frame(data):
    global latest_frame
    global detection_count_facial, detection_count_objetos, detection_count_poses
    global activity_logs_facial, activity_logs_objetos, activity_logs_poses

    latest_frame = data['frame'] 

    # Simulación de detecciones
    detection_count_facial += 1
    detection_count_objetos += 1
    detection_count_poses += 1

    activity_logs_facial.append(f"Detección Facial #{detection_count_facial}")
    activity_logs_objetos.append(f"Detección Objetos #{detection_count_objetos}")
    activity_logs_poses.append(f"Detección Poses #{detection_count_poses}")

sio.connect('http://127.0.0.1:5000')

app.layout = dbc.Container(
    [
        html.H1("Registro Facial", style={'textAlign': 'center', 'color': 'white'}),
        dbc.Tabs(
            [
                dbc.Tab(label="Registros", tab_id="registros"),
                dbc.Tab(label="Cámaras", tab_id="camaras"),
            ],
            id="tabs",
            active_tab="registros",
            style={'marginBottom': '20px'}
        ),
        html.Div(id="tab-content", style={'backgroundColor': '#2C2C2C', 'height': '100%'}),
    ],
    fluid=True,
    style={'backgroundColor': '#2C2C2C', 'height': '100vh'}
)

@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "registros":
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Upload(
                                    id='upload-image',
                                    children=html.Div([
                                        'Arrastra y suelta o ',
                                        html.A('Selecciona una Imagen', style={'color': '#2CA8FF'})
                                    ]),
                                    style={
                                        'width': '100%',
                                        'height': '60px',
                                        'lineHeight': '60px',
                                        'borderWidth': '1px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        'margin': '10px',
                                        'color': 'white'
                                    },
                                    multiple=False
                                ),
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Imagen Cargada", style={'color': 'white', 'backgroundColor': '#1C1C1C'}),
                                        dbc.CardBody(
                                            html.Div(
                                                id='original-image',
                                                style={
                                                    'width': '100%',
                                                    'height': '300px',
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
                                        'border': '1px solid #444'
                                    }
                                ),
                            ],
                            width=6
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader("Registro de Persona", style={'color': 'white', 'backgroundColor': '#1C1C1C'}),
                                        dbc.CardBody(
                                            [
                                                dbc.Input(
                                                    id="input-name",
                                                    placeholder="Ingresa tu nombre",
                                                    type="text",
                                                    style={'marginBottom': '10px'}
                                                ),
                                                dbc.Button(
                                                    "Guardar",
                                                    id="save-button",
                                                    color="primary",
                                                    style={'marginBottom': '10px'}
                                                ),
                                                html.Div(id='output-message', style={'marginTop': '10px'})
                                            ],
                                            style={'backgroundColor': '#2C2C2C'}
                                        ),
                                    ],
                                    style={
                                        'margin': '10px',
                                        'backgroundColor': '#2C2C2C',
                                        'border': '1px solid #444'
                                    }
                                ),
                            ],
                            width=6
                        ),
                    ]
               ),
                html.Hr(),
                html.H4("Lista de Registros", style={'color': 'white', 'textAlign': 'center', 'marginTop': '20px'}),
                html.Div(id="records-table", style={'margin': '20px'})
            ]
        )

    elif active_tab == "camaras":
        return html.Div(
            [
                html.H4("Stream de Cámaras", style={'color': 'white', 'textAlign': 'center'}),

                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Reconocimiento Facial", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Img(
                                        id="video-feed-1",
                                        style={
                                            'width': '1280px',
                                            'height': '720px',
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
                            width=4
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Cámara YOLO", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Canvas(
                                        id="videoCanvas",
                                        style={
                                            'width': '1280px',
                                            'height': '720px',
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
                            width=4
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H5("Reconocimiento de Poses", style={'color': 'white', 'textAlign': 'center'}),
                                    html.Img(
                                        id="video-feed-3",
                                        style={
                                            'width': '1280px',
                                            'height': '720px',
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
                            width=4
                        ),
                    ]
                ),

                html.H4("Registro de Actividad", style={'color': 'white', 'textAlign': 'center', 'marginTop': '20px'}),

                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                id="activity-log-facial",
                                style={
                                    'color': 'white',
                                    'border': '1px solid white',
                                    'borderRadius': '10px',
                                    'padding': '10px',
                                    'overflowY': 'auto',
                                    'height': '300px'
                                }
                            ), width=4
                        ),
                        dbc.Col(
                            html.Div(
                                id="activity-log-objetos",
                                style={
                                    'color': 'white',
                                    'border': '1px solid white',
                                    'borderRadius': '10px',
                                    'padding': '10px',
                                    'overflowY': 'auto',
                                    'height': '300px'
                                }
                            ), width=4
                        ),
                        dbc.Col(
                            html.Div(
                                id="activity-log-poses",
                                style={
                                    'color': 'white',
                                    'border': '1px solid white',
                                    'borderRadius': '10px',
                                    'padding': '10px',
                                    'overflowY': 'auto',
                                    'height': '300px'
                                }
                            ), width=4
                        ),
                    ],
                    style={'marginTop': '20px'}
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(id="activity-graph", style={'height': '300px'}),
                            width=12
                        )
                    ],
                    style={'marginTop': '20px'}
                ),

                dcc.Interval(id="interval", interval=1000),
            ]
        )
    return "Seleccione una pestaña para ver el contenido."

@app.callback(
    [Output("video-feed-1", "src"), Output("videoCanvas", "children"), Output("video-feed-3", "src")],
    [Input("interval", "n_intervals"), Input("tabs", "active_tab")]
)
def update_frame(_, active_tab):
    if active_tab != "camaras":
        return dash.no_update, dash.no_update, dash.no_update
    global latest_frame
    if latest_frame:
        src_value = f"data:image/jpeg;base64,{latest_frame}"
        return src_value, None, src_value  # El segundo elemento corresponde a videoCanvas
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    [Output('original-image', 'children')],
    [Input('upload-image', 'contents')],
    [State('upload-image', 'filename')]
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
        return [image]
    return [None]

@app.callback(
    Output('output-message', 'children'),
    [Input('save-button', 'n_clicks')],
    [State('upload-image', 'contents'), State('input-name', 'value')]
)
def enviar_datos_backend(n_clicks, image_content, name):
    if n_clicks:
        if image_content and name:
            image_data = image_content.split(",")[1]
            payload = {
                'name': name,
                'image': image_data
            }
            try:
                response = requests.post('http://127.0.0.1:5000/register', json=payload)
                if response.status_code == 200:
                    # Mostrar alerta de éxito
                    return dbc.Alert("Registro exitoso.", color="success", duration=3000)
                else:
                    return dbc.Alert(
                        f"Error del backend: {response.json().get('error', 'Error desconocido')}",
                        color="danger"
                    )
            except Exception as e:
                return dbc.Alert(
                    f"Error de conexión con el backend: {e}",
                    color="danger"
                )
        else:
            return dbc.Alert("Por favor, carga una imagen y escribe un nombre.", color="warning")
    return ""

@app.callback(
    Output("records-table", "children"),
    Input("tabs", "active_tab")
)
def update_records_table(active_tab):
    if active_tab == "registros":
        try:
            response = requests.get("http://127.0.0.1:5000/get_records")
            if response.status_code == 200:
                records = response.json()
                if not records:
                    return html.Div("No hay registros disponibles.", style={'color': 'white', 'textAlign': 'center'})
                
                table_header = [
                    html.Thead(html.Tr([html.Th("ID"), html.Th("Persona"), html.Th("Fecha")]))
                ]
                table_body = html.Tbody([
                    html.Tr([
                        html.Td(record["id"]),
                        html.Td(record["persona"]),
                        html.Td(record["fecha"]),
                    ]) for record in records
                ])

                return dbc.Table(
                    table_header + [table_body],
                    bordered=True,
                    dark=True,
                    hover=True,
                    responsive=True,
                    striped=True,
                    style={'color': 'white', 'backgroundColor': '#2C2C2C'}
                )
            else:
                return html.Div("Error al obtener registros.", style={'color': 'white', 'textAlign': 'center'})
        except Exception as e:
            return html.Div(f"Error de conexión: {e}", style={'color': 'white', 'textAlign': 'center'})
    return ""

@app.callback(
    [Output('activity-log-facial', 'children'),
     Output('activity-log-objetos', 'children'),
     Output('activity-log-poses', 'children'),
     Output('activity-graph', 'figure')],
    [Input('interval', 'n_intervals'), Input('tabs', 'active_tab')]
)
def update_activity(_, active_tab):
    if active_tab != "camaras":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    global activity_logs_facial, activity_logs_objetos, activity_logs_poses
    global detection_count_facial, detection_count_objetos, detection_count_poses

    logs_facial_display = [html.Div(log) for log in activity_logs_facial[-50:]]
    logs_objetos_display = [html.Div(log) for log in activity_logs_objetos[-50:]]
    logs_poses_display = [html.Div(log) for log in activity_logs_poses[-50:]]

    x_values = ["Facial", "Objetos", "Poses"]
    y_values = [detection_count_facial, detection_count_objetos, detection_count_poses]

    fig = go.Figure(data=[go.Bar(x=x_values, y=y_values, marker_color=['#2ca02c','#1f77b4','#d62728'])])
    fig.update_layout(
        title="Conteo de Detecciones",
        xaxis_title="Tipo de Reconocimiento",
        yaxis_title="Conteo",
        template="plotly_dark",
        paper_bgcolor='#2C2C2C',
        plot_bgcolor='#2C2C2C',
        font_color='white'
    )

    return logs_facial_display, logs_objetos_display, logs_poses_display, fig

if __name__ == '__main__':
    app.run_server(debug=True)
