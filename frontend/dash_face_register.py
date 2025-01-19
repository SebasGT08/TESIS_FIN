import dash
from dash import html, dcc, Input, Output, State,MATCH,ALL,callback_context
import dash_bootstrap_components as dbc
#import socketio
import requests
import plotly.graph_objects as go
from dateutil import parser
import ast
# --------------------------------------------------------------------
# HTML incrustado para las cámaras con sidebar, miniaturas, y lógica
# --------------------------------------------------------------------
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YOLO & Pose Detection Streams - Vista DVR</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1D1F21;
            font-family: Arial, sans-serif;
            color: #fff;
            display: flex;
            flex-direction: row;
            height: 100vh;
        }
        /* Sidebar */
        .sidebar {
            width: 280px;
            background-color: #2E2E2E;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
        }
        .sidebar h2 {
            margin-bottom: 20px;
        }
        .controls {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }
        .controls button {
            background-color: #007bff;
            border: none;
            color: white;
            font-size: 16px;
            padding: 8px 15px;
            cursor: pointer;
            border-radius: 5px;
        }
        .controls button:hover {
            background-color: #0056b3;
        }
        .sidebar button#viewAllBtn {
            width: 100%;
            padding: 12px;
            margin-bottom: 20px;
            background-color: #28a745; /* Verde */
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
        }
        .sidebar button#viewAllBtn:hover {
            background-color: #218838;
        }
        .camera-list {
            width: 100%;
        }
        .camera-item {
            background-color: #3A3A3A;
            padding: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            text-align: center;
            border-radius: 5px;
        }
        .camera-item:hover {
            background-color: #4A4A4A;
        }
        .mini-thumb {
            display: block;
            margin: 0 auto 5px auto; 
            border: 1px solid #000;
            width: 120px; 
            height: 90px; 
        }

        /* Main view */
        .main-view {
            flex: 1;
            background-color: #1D1F21;
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap; /* Para mantenerlas en una fila */
            justify-content: center;
            align-items: center;
            position: relative;
        }
        /* En modo "Ver Todo" */
        .multi-camera .camera-view {
            width: 32%;
            margin: 5px;
            box-sizing: border-box;
            border: 1px solid #444;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
        }
        /* En modo "una sola cámara" */
        .single-camera .camera-view {
            width: 95%;
            height: 90%;
            margin: 0 auto;
            border: 1px solid #444;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
        }
        .camera-title {
            background-color: #333;
            width: 100%;
            text-align: center;
            padding: 5px;
            font-weight: bold;
        }
        canvas {
            max-width: 100%;
            max-height: calc(100% - 30px);
        }
        /* Ocultar cámaras */
        .hidden {
            display: none !important;
        }

    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Lista de Cámaras</h2>

        <!-- Controles con flechas -->
        <div class="controls">
            <button id="prevCameraBtn">&#8592;</button>
            <button id="nextCameraBtn">&#8594;</button>
        </div>

        <!-- Botón para ver todas las cámaras -->
        <button id="viewAllBtn">Ver Todo</button>

        <div class="camera-list">
            <div class="camera-item" onclick="showSingleCamera('poseContainer')">
                <!-- Miniatura de la cámara de Poses -->
                <canvas id="poseThumbCanvas" class="mini-thumb"></canvas>
                <span>Cámara Poses</span>
            </div>
            <div class="camera-item" onclick="showSingleCamera('objectContainer')">
                <!-- Miniatura de la cámara de Objetos -->
                <canvas id="objectThumbCanvas" class="mini-thumb"></canvas>
                <span>Cámara Objetos</span>
            </div>
            <div class="camera-item" onclick="showSingleCamera('faceContainer')">
                <!-- Miniatura de la cámara de Rostros -->
                <canvas id="faceThumbCanvas" class="mini-thumb"></canvas>
                <span>Cámara Rostros</span>
            </div>
        </div>
    </div>

    <div class="main-view multi-camera" id="mainView">
        <!-- Cámara de Poses -->
        <div class="camera-view" id="poseContainer">
            <div class="camera-title">Detección de Poses</div>
            <canvas id="poseCanvas"></canvas>
        </div>
        <!-- Cámara de Objetos -->
        <div class="camera-view" id="objectContainer">
            <div class="camera-title">Detección de Objetos</div>
            <canvas id="objectCanvas"></canvas>
        </div>
        <!-- Cámara de Rostros -->
        <div class="camera-view" id="faceContainer">
            <div class="camera-title">Detección de Rostros</div>
            <canvas id="faceCanvas"></canvas>
        </div>
    </div>

    <script>
        // ----- WebSocket Initialization for main view -----
        function initWebSocket(canvasId, websocketUrl) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext("2d");
            const socket = new WebSocket(websocketUrl);
            const image = new Image();

            socket.binaryType = "arraybuffer";
            socket.onmessage = (event) => {
                const blob = new Blob([event.data], { type: "image/jpeg" });
                const url = URL.createObjectURL(blob);
                image.onload = () => {
                    canvas.width = image.width;
                    canvas.height = image.height;
                    ctx.drawImage(image, 0, 0);
                    URL.revokeObjectURL(url);
                };
                image.src = url;
            };
            socket.onerror = (error) => {
                console.error(`Error en el WebSocket (${websocketUrl}):`, error);
            };
            socket.onclose = () => {
                console.log(`Conexión WebSocket cerrada (${websocketUrl})`);
            };
        }

        // ----- WebSocket Initialization for thumbnails -----
        function initWebSocketThumb(canvasId, websocketUrl) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext("2d");
            const socket = new WebSocket(websocketUrl);
            const image = new Image();

            socket.binaryType = "arraybuffer";
            socket.onmessage = (event) => {
                const blob = new Blob([event.data], { type: "image/jpeg" });
                const url = URL.createObjectURL(blob);
                image.onload = () => {
                    // Ajustamos el tamaño del lienzo al tamaño de la miniatura
                    canvas.width = 120; 
                    canvas.height = 90; 
                    // Dibuja la imagen ajustada a la miniatura
                    ctx.drawImage(image, 0, 0, 120, 90);
                    URL.revokeObjectURL(url);
                };
                image.src = url;
            };
            socket.onerror = (error) => {
                console.error(`Error en WebSocket THUMB (${websocketUrl}):`, error);
            };
            socket.onclose = () => {
                console.log(`Conexión WebSocket cerrada (THUMB) (${websocketUrl})`);
            };
        }

        // Inicializar WebSockets para vistas principales
        initWebSocket("poseCanvas", "ws://localhost:8000/ws/poses");
        initWebSocket("objectCanvas", "ws://localhost:8000/ws/objects");
        initWebSocket("faceCanvas", "ws://localhost:8000/ws/faces");

        // Inicializar WebSockets para miniaturas
        initWebSocketThumb("poseThumbCanvas", "ws://localhost:8000/ws/poses");
        initWebSocketThumb("objectThumbCanvas", "ws://localhost:8000/ws/objects");
        initWebSocketThumb("faceThumbCanvas", "ws://localhost:8000/ws/faces");

        // ----- IDs de cámaras principales -----
        const cameras = ["poseContainer", "objectContainer", "faceContainer"];
        let currentIndex = 0;

        const mainView = document.getElementById("mainView");

        // Mostrar todas las cámaras en modo horizontal
        function showAllCameras() {
            mainView.classList.add("multi-camera");
            mainView.classList.remove("single-camera");

            // Mostramos todas las cámaras
            cameras.forEach((camId) => {
                document.getElementById(camId).classList.remove("hidden");
            });
        }

        // Mostrar cámara única en fullscreen
        function showSingleCamera(containerId) {
            mainView.classList.remove("multi-camera");
            mainView.classList.add("single-camera");

            // Ocultamos todas menos la seleccionada
            cameras.forEach((camId) => {
                document.getElementById(camId).classList.add("hidden");
            });
            document.getElementById(containerId).classList.remove("hidden");

            // Actualizamos el currentIndex
            currentIndex = cameras.indexOf(containerId);
        }

        // Botón "Ver Todo"
        document.getElementById("viewAllBtn").addEventListener("click", () => {
            showAllCameras();
        });

        // Botones de navegación (flechas)
        document.getElementById("prevCameraBtn").addEventListener("click", () => {
            // Si estamos en single-camera, vamos a la anterior
            if (mainView.classList.contains("single-camera")) {
                currentIndex = (currentIndex - 1 + cameras.length) % cameras.length;
                showSingleCamera(cameras[currentIndex]);
            }
        });

        document.getElementById("nextCameraBtn").addEventListener("click", () => {
            // Si estamos en single-camera, vamos a la siguiente
            if (mainView.classList.contains("single-camera")) {
                currentIndex = (currentIndex + 1) % cameras.length;
                showSingleCamera(cameras[currentIndex]);
            }
        });

        // Tecla flecha derecha e izquierda
        document.addEventListener("keydown", (event) => {
            // Para que funcione, debes hacer clic dentro del iframe y luego presionar la tecla
            if (mainView.classList.contains("single-camera")) {
                if (event.key === "ArrowRight") {
                    // siguiente
                    currentIndex = (currentIndex + 1) % cameras.length;
                    showSingleCamera(cameras[currentIndex]);
                }
                else if (event.key === "ArrowLeft") {
                    // anterior
                    currentIndex = (currentIndex - 1 + cameras.length) % cameras.length;
                    showSingleCamera(cameras[currentIndex]);
                }
            }
        });
    </script>
</body>
</html>
"""

login_layout = dbc.Container(
    [
        html.Div(
            [
                html.H1("Inicio de Sesión", style={'textAlign': 'center', 'color': 'white'}),
                dbc.Input(id="login-usuario", placeholder="Usuario", type="text", style={'marginBottom': '10px'}),
                dbc.Input(id="login-password", placeholder="Contraseña", type="password", style={'marginBottom': '10px'}),
                dbc.Button("Iniciar Sesión", id="btn-login", color="primary", style={'width': '100%'}),
                # Espacio para mensajes dinámicos
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

# ----------------------------------------------------
# Configuración inicial de la app Dash
# ----------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
    ],
    suppress_callback_exceptions=True
)
app.title = 'Registro Facial'

#sio = socketio.Client()

latest_frame = None
activity_logs_facial = []
activity_logs_objetos = []
activity_logs_poses = []
detection_count_facial = 0
detection_count_objetos = 0
detection_count_poses = 0


# --------------------------------------------------------------------------------------
# (Opcional) Evento de Socket.IO, si lo usas con tu backend (comentado por defecto)
# --------------------------------------------------------------------------------------
# @sio.on('video_frame')
# def handle_video_frame(data):
#     global latest_frame
#     global detection_count_facial, detection_count_objetos, detection_count_poses
#     global activity_logs_facial, activity_logs_objetos, activity_logs_poses
#
#     latest_frame = data['frame']
#     detection_count_facial += 1
#     detection_count_objetos += 1
#     detection_count_poses += 1
#
#     activity_logs_facial.append(f"Detección Facial #{detection_count_facial}")
#     activity_logs_objetos.append(f"Detección de Objetos #{detection_count_objetos}")
#     activity_logs_poses.append(f"Detección de Poses #{detection_count_poses}")
#
# sio.connect('http://127.0.0.1:5000')
def build_users_table():
    """
    Llama al endpoint /get_users del backend,
    crea y retorna la tabla con la lista de usuarios.
    """
    try:
        response = requests.get("http://127.0.0.1:5000/get_users")
        if response.status_code == 200:
            users = response.json()
            if not users:
                return html.Div(
                    "No hay usuarios registrados.",
                    style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
                )

            def format_datetime(fecha_str):
                try:
                    dt = parser.parse(fecha_str)
                    return dt.strftime('%d/%m/%Y %I:%M %p')  # Ej: "22/01/2025 02:05 PM"
                except:
                    return fecha_str

            table_header = [
                html.Thead(
                    html.Tr([
                        html.Th("ID", style={'width': '10%', 'fontSize': '16px'}),
                        html.Th("Nombre", style={'width': '20%', 'fontSize': '16px'}),
                        html.Th("Usuario", style={'width': '20%', 'fontSize': '16px'}),
                        html.Th("Contraseña", style={'width': '20%', 'fontSize': '16px'}),
                        html.Th("Tipo", style={'width': '10%', 'fontSize': '16px'}),
                        html.Th("Estado", style={'width': '10%', 'fontSize': '16px'}),
                        html.Th("Acciones", style={'width': '10%', 'fontSize': '16px'}),
                    ])
                )
            ]

            table_body = html.Tbody([
                html.Tr([
                    html.Td(user["id"], style={'fontSize': '14px'}),
                    html.Td(user["nombre"], style={'fontSize': '14px'}),
                    html.Td(user["usuario"], style={'fontSize': '14px'}),
                    html.Td(
                        [
                            dbc.Input(
                                id={'type': 'password-field', 'index': user["id"]},
                                type="password",
                                value=user["password"],
                                readonly=True,
                                style={'fontSize': '14px', 'width': '80%', 'marginRight': '5px'}
                            ),
                            dbc.Button(
                                html.I(className="fas fa-eye"),
                                id={'type': 'toggle-password', 'index': user["id"]},
                                color="secondary",
                                size="sm",
                                style={'marginTop': '-5px'}
                            )
                        ],
                        style={'display': 'flex', 'alignItems': 'center'}
                    ),
                    html.Td(
                        "Administrador" if user["tipo"] == "A" else "Empleado",
                        style={'fontSize': '14px'}
                    ),
                    html.Td(
                        "Activo" if user["estado"] == "A" else "Inactivo",
                        style={'fontSize': '14px'}
                    ),
                    html.Td(
                        [
                            dbc.Button(
                                "Editar",
                                id={'type': 'edit-user', 'index': user["id"]},
                                color="warning",
                                size="sm",
                                style={'marginRight': '5px'}
                            ),
                            # Botón "Eliminar" con ConfirmDialogProvider
                            dcc.ConfirmDialogProvider(
                                dbc.Button(
                                    "Eliminar",
                                    id={'type': 'delete-user-button', 'index': user["id"]},
                                    color="danger",
                                    size="sm"
                                ),
                                id={'type': 'confirm-delete-provider-user', 'index': user["id"]},  # Tipo único para usuarios
                                message=f"¿Estás seguro de que deseas eliminar al usuario {user['nombre']}?"
                            ),
                        ],
                        style={'textAlign': 'center'}
                    ),
                ]) for user in users
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
                    'width': '90%',
                    'margin': '0 auto'
                }
            )
        else:
            return html.Div(
                "Error al obtener usuarios del backend.",
                style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
            )
    except Exception as e:
        return html.Div(
            f"Error de conexión: {e}",
            style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
        )

import ast
from dash import callback_context



@app.callback(
    Output({'type': 'users-table-container', 'index': 'unique'}, 'children'),  # Para la tabla de usuarios
    Input("modal-users-table", "is_open"),
    Input('users-update-store', 'data'),  # Disparador para actualizar la tabla
    prevent_initial_call=True
)
def update_users_table(is_open, update_trigger):
    if is_open:
        # Cargar y retornar la tabla de usuarios
        return build_users_table()
    else:
        raise dash.exceptions.PreventUpdate
@app.callback(
    [
        Output('users-table-feedback', 'children'),
        Output('users-update-store', 'data')
    ],
    [
        Input({'type': 'confirm-delete-provider-user', 'index': MATCH}, 'submit_n_clicks')
    ],
    [
        State({'type': 'confirm-delete-provider-user', 'index': MATCH}, 'index'),
        State('users-update-store', 'data')
    ],
    prevent_initial_call=True
)
def delete_user(submit_n_clicks, user_id, update_trigger):
    if submit_n_clicks and submit_n_clicks > 0:
        try:
            # Enviar solicitud DELETE al backend
            response = requests.delete(
                "http://127.0.0.1:5000/delete_usuario",
                json={"id": user_id}
            )
            if response.status_code == 200:
                feedback = dbc.Alert("Usuario eliminado exitosamente.", color="success", dismissable=True)
                new_store_value = (int(update_trigger) if isinstance(update_trigger, int) else 0) + 1
                return feedback, new_store_value
            else:
                error_msg = response.json().get("error", f"Error {response.status_code}")
                feedback = dbc.Alert(f"Ocurrió un error al eliminar el usuario: {error_msg}", color="danger", dismissable=True)
                return feedback, dash.no_update
        except Exception as e:
            feedback = dbc.Alert(f"Error al procesar la eliminación: {str(e)}", color="danger", dismissable=True)
            return feedback, dash.no_update
    else:
        raise dash.exceptions.PreventUpdate


@app.callback(
    Output({'type': 'password-field', 'index': MATCH}, 'type'),
    Input({'type': 'toggle-password', 'index': MATCH}, 'n_clicks'),
    State({'type': 'password-field', 'index': MATCH}, 'type')
)
def toggle_password_visibility(n_clicks, current_type):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    return 'text' if current_type == 'password' else 'password'

# --------------------------------------------------------------------------------------
# Función auxiliar para construir la tabla de registros
# --------------------------------------------------------------------------------------

def format_date(fecha):
    """Formatea la fecha al formato dd/mm/yyyy HH:MM AM/PM."""
    try:
        dt = parser.parse(fecha)
        return dt.strftime('%d/%m/%Y %I:%M %p')  # Ejemplo: "22/01/2025 02:05 PM"
    except:
        return fecha

def build_records_table(records):
    """
    Construye la tabla con barra de búsqueda, scroll y columna de estado.
    """
    # Manejar caso de registros vacíos
    if not records:
        return html.Div(
            "No hay registros disponibles.",
            style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
        )

    # Cabecera de la tabla
    table_header = [
        html.Thead(
            html.Tr([
                html.Th("ID", style={'width': '10%', 'fontSize': '18px'}),
                html.Th("Persona", style={'width': '30%', 'fontSize': '18px'}),
                html.Th("Fecha", style={'width': '30%', 'fontSize': '18px'}),
                html.Th("Estado", style={'width': '15%', 'fontSize': '18px'}),
                html.Th("Acciones", style={'width': '15%', 'fontSize': '18px'}),
            ])
        )
    ]

    # Cuerpo de la tabla
    def create_table_body(filtered_records):
        return html.Tbody([
            html.Tr([
                html.Td(record["id"], style={'fontSize': '16px'}),
                html.Td(record["persona"], style={'fontSize': '16px'}),
                html.Td(format_date(record["fecha"]), style={'fontSize': '16px'}),
                html.Td(
                    "Activo" if record["estado"] == "A" else "Inactivo",
                    style={'fontSize': '16px', 'color': 'green' if record["estado"] == "A" else 'red'}
                ),
                html.Td(
                    [
                        dbc.Button(
                            "Editar",
                            id={'type': 'edit-record', 'index': record["id"]},
                            color="warning",
                            size="sm",
                            style={'marginRight': '5px'}
                        ),
                      dcc.ConfirmDialogProvider(
                            dbc.Button(
                                "Eliminar",
                                id={'type': 'delete-record-button', 'index': record["id"]},
                                color="danger",
                                size="sm"
                            ),
                            id={'type': 'confirm-delete-provider-record', 'index': record["id"]},  # Tipo único para registros
                            message=f"¿Estás seguro de que deseas eliminar el registro {record['persona']}?"
                        ),

                    ],
                    style={'textAlign': 'center'}
                ),
            ]) for record in filtered_records
        ])

    table = html.Div(
        [
            dbc.InputGroup(
                [
                    dbc.Input(
                        id="search-bar",
                        type="text",
                        placeholder="Buscar por nombre o fecha (dd/mm/yyyy)",
                        style={'fontSize': '16px'}
                    ),
                    dbc.InputGroupText(html.I(className="fas fa-search")),
                ],
                className="mb-3",
                style={'width': '50%', 'marginLeft': '25%'}
            ),
            dbc.Table(
                table_header + [create_table_body(records)],
                bordered=True,
                dark=True,
                hover=True,
                responsive=True,
                striped=True,
                style={
                    'color': 'white',
                    'backgroundColor': '#2C2C2C',
                    'fontSize': '18px',
                    'width': '100%'
                }
            )
        ],
        style={
            'maxHeight': '300px',  # Limitar altura para scroll
            'overflowY': 'scroll',
            'margin': '0 auto'
        }
    )
    return table

# --------------------------------------------------------------------------------------
# Layout principal de la app
# --------------------------------------------------------------------------------------
app_layout = dbc.Container(
    [
        html.H1("Registro Facial", style={'textAlign': 'center', 'color': 'white', 'marginTop': '20px'}),
        dbc.Row(
            [
                # Columna para los Tabs
                dbc.Col(
                    dbc.Tabs(
                        [
                            dbc.Tab(label="Registros", tab_id="registros"),
                            dbc.Tab(label="Cámaras", tab_id="camaras"),
                        ],
                        id="tabs",
                        active_tab="registros",
                        style={'marginBottom': '0px'}  # Elimina el margen inferior de los tabs
                    ),
                    width=9  # Espacio asignado a los tabs
                ),
                # Columna para el botón "Salir"
                dbc.Col(
                    dbc.Button("Salir", id="logout-button", color="danger", style={'float': 'right'}),
                    width=3,  # Espacio asignado al botón
                    style={'textAlign': 'right'}  # Alinea el contenido a la derecha
                ),
            ],
            align="center",  # Alinea verticalmente al centro
            justify="between",  # Espacia los elementos horizontalmente
            style={'marginBottom': '20px'}  # Espacio debajo del row
        ),
        # Contenido dinámico de cada pestaña
        html.Div(id="tab-content", style={'backgroundColor': '#2C2C2C', 'height': '100%'}),

        # Intervalo para refrescar datos (cámaras, actividad)
        dcc.Interval(id="interval", interval=2000),
        dcc.Store(id='users-update-store', data=0),
         html.Div(id='dummy-output', style={'display': 'none'}),


    ],
    fluid=True,
    style={'backgroundColor': '#2C2C2C', 'height': '100vh', 'padding': '20px'}
)


app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),  # Controla la ruta actual
        html.Div(id="page-content")  # Contenido dinámico basado en la ruta
    ],
    fluid=True,
    style={'backgroundColor': '#2C2C2C', 'height': '100vh'}
)

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/app":
        return app_layout  # Muestra el layout principal
    return login_layout  # Muestra el login si no está autenticado
@app.callback(
    [Output("url", "pathname"), Output("login-feedback", "children")],
    Input("btn-login", "n_clicks"),
    [State("login-usuario", "value"), State("login-password", "value")]
)
def handle_login(btn_login_clicks, usuario, password):
    if not btn_login_clicks:
        raise dash.exceptions.PreventUpdate

    # Validación mínima
    if not usuario or not password:
        return dash.no_update, "Por favor ingrese usuario y contraseña."

    # Simula el llamado al backend para validar credenciales
    try:
        response = requests.post(
            "http://127.0.0.1:5000/login_user",
            json={"usuario": usuario, "password": password}
        )
        if response.status_code == 200:
            # Login exitoso
            return "/app", ""
        else:
            # Credenciales inválidas
            return dash.no_update, "Credenciales incorrectas. Inténtelo de nuevo."
    except Exception:
        # Error de conexión al backend
        return dash.no_update, "Error al conectar con el servidor. Inténtelo más tarde."

@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_logout(btn_logout_clicks):
    if not btn_logout_clicks:
        raise dash.exceptions.PreventUpdate

    # Simula un logout exitoso
    return "/login"


dbc.Button("Iniciar Sesión", id="btn-login", color="primary", style={'width': '100%'})


# --------------------------------------------------------------------------------------
# Callback para renderizar el contenido de cada Tab
# --------------------------------------------------------------------------------------
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "registros":
        try:
            # Llamar al backend para obtener registros
            response = requests.get("http://127.0.0.1:5000/get_records")
            if response.status_code == 200:
                records = response.json()
            else:
                return html.Div(
                    f"Error al obtener registros: {response.status_code}",
                    style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
                )
        except Exception as e:
            return html.Div(
                f"Error de conexión con el backend: {str(e)}",
                style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
            )

        # Llamar a build_records_table con los registros obtenidos
        records_table = build_records_table(records)

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
                                                        style={'marginBottom': '10px', 'fontSize': '18px', 'width': '70%', 'height': '50px'}
                                                    ),
                                                    html.Div(
                                                        [
                                                            dbc.Spinner(
                                                                html.Div(id='output-message'),
                                                                size="sm",  # Tamaño del spinner (pequeño)
                                                                color="primary",  # Color del spinner
                                                                type="border",  # Estilo de spinner
                                                                fullscreen=False,  # No ocupa toda la pantalla
                                                            )
                                                        ],
                                                        style={'marginTop': '30px', 'fontSize': '16px'}
                                                    ),

                                                html.Hr(),
                                                # BOTÓN: Registrar Usuario
                                                dbc.Button(
                                                    [
                                                        html.I(className="fas fa-user", style={"marginRight": "5px"}),
                                                        "Registrar Usuario"
                                                    ],
                                                    id="open-user-modal",
                                                    color="success",
                                                    style={'fontSize':'18px','width':'70%','marginTop':'10px'}
                                                ),
                                                # BOTÓN: Ver Usuarios
                                                dbc.Button(
                                                    [
                                                        html.I(className="fa fa-search", style={"marginRight":"5px"}),
                                                        " Ver Usuarios"
                                                    ],
                                                    id="open-users-table-modal",
                                                    color="info",
                                                    style={'fontSize':'18px','width':'70%','marginTop':'10px'}
                                                )
                                            ],
                                            style={'backgroundColor':'#2C2C2C'}
                                        ),
                                    ],
                                    style={
                                        'margin':'10px',
                                        'backgroundColor':'#2C2C2C',
                                        'border':'2px solid #444'
                                    }
                                )
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
                ),

                    # ----------------------------------------------------------------
                    # Modal para crear usuario
                    # ----------------------------------------------------------------
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle("Registrar Nuevo Usuario")),
                            dbc.ModalBody(
                                [
                                    dbc.Label("Nombre Completo", style={'fontSize': '16px'}),
                                    dbc.Input(
                                        id="reg-nombre",
                                        type="text",
                                        placeholder="Ingresa nombre completo",
                                        style={'marginBottom': '15px'}
                                    ),
                                    
                                    dbc.Label("Usuario", style={'fontSize': '16px'}),
                                    dbc.Input(
                                        id="reg-usuario",
                                        type="text",
                                        placeholder="Ingresa usuario",
                                        style={'marginBottom': '15px'}
                                    ),
                                    
                                    dbc.Label("Contraseña", style={'fontSize': '16px'}),
                                    dbc.Input(
                                        id="reg-password",
                                        type="password",
                                        placeholder="Ingresa contraseña",
                                        style={'marginBottom': '15px'}
                                    ),
                                    
                                    dbc.Label("Confirmar Contraseña", style={'fontSize': '16px'}),
                                    dbc.Input(
                                        id="reg-password2",
                                        type="password",
                                        placeholder="Repite la contraseña",
                                        style={'marginBottom': '15px'}
                                    ),
                                    
                                    dbc.Label("Tipo de Usuario", style={'fontSize': '16px'}),
                                    dcc.Dropdown(
                                        id="reg-tipo", 
                                        options=[
                                            {"label": "Administrador", "value": "A"},
                                            {"label": "Empleado", "value": "E"}
                                        ],
                                        placeholder="Selecciona el tipo de usuario",
                                        style={'marginBottom': '15px'}
                                    ),
                                    
                                    # Mensajes de error/éxito
                                    html.Div(id="reg-user-msg", style={'marginTop': '10px'})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button("Guardar", id="btn-save-user", color="primary")
                            ),
                        ],
                        id="modal-user-registration",
                        is_open=False,
                        size="md",
                        centered=True,
                    ),

                                # ----------------------------------------------------------------
                    # Modal con la tabla de usuarios
                    # ----------------------------------------------------------------
                    # Modal con la tabla de usuarios
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle("Lista de Usuarios")),
                            dbc.ModalBody(
                                [
                                    # Contenedor para mensajes de alerta
                                    html.Div(
                                        id='users-table-feedback',
                                        children=[],  # Vacío inicialmente
                                        style={'marginBottom': '10px'}
                                    ),
                                    # Contenedor donde se muestra la tabla
                                    html.Div(
                                        id={'type': 'users-table-container', 'index': 'unique'},
                                        children=[]  # Vacío inicialmente
                                    )
                                ]
                            )
                        ],
                        id="modal-users-table",
                        is_open=False,
                        size="xl",
                        centered=True,
                        scrollable=True
                    ),


                # ----------------------------------------------------------------
                # Modal para EDITAR USUARIO
                # ----------------------------------------------------------------
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Editar Usuario")),
                        dbc.ModalBody(
                            [
                                # Campo oculto con el ID
                                dbc.Input(id="edit-user-id", type="hidden"),

                                dbc.Label("Nombre Completo", style={'fontSize': '16px'}),
                                dbc.Input(
                                    id="edit-nombre",
                                    type="text",
                                    placeholder="Nombre completo",
                                    style={'marginBottom': '15px'}
                                ),

                                dbc.Label("Usuario", style={'fontSize': '16px'}),
                                dbc.Input(
                                    id="edit-usuario",
                                    type="text",
                                    placeholder="Usuario",
                                    style={'marginBottom': '15px'}
                                ),

                                dbc.Label("Contraseña", style={'fontSize': '16px'}),
                                dbc.Input(
                                    id="edit-password",
                                    type="password",
                                    placeholder="Contraseña",
                                    style={'marginBottom': '15px'}
                                ),

                                dbc.Label("Confirmar Contraseña", style={'fontSize': '16px'}),
                                dbc.Input(
                                    id="edit-password2",
                                    type="password",
                                    placeholder="Repite la contraseña",
                                    style={'marginBottom': '15px'}
                                ),

                                dbc.Label("Tipo de Usuario", style={'fontSize': '16px'}),
                                dcc.Dropdown(
                                    id="edit-tipo",
                                    options=[
                                        {"label": "Administrador", "value": "A"},
                                        {"label": "Empleado", "value": "E"}
                                    ],
                                    style={'marginBottom':'15px'}
                                ),

                                # Mensaje de validación / error / éxito
                                html.Div(id="edit-user-msg", style={'marginTop':'10px'})
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Actualizar", id="btn-update-user", color="primary")
                        ),
                    ],
                    id="modal-edit-user",
                    is_open=False,
                    size="md",
                    centered=True,
                ),
            ]
        )

    elif active_tab == "camaras":
        # Nueva interfaz estilo DVR en el Iframe
        return html.Div(
            style={'padding': '20px'},
            children=[
                html.H4(
                    "Stream de Cámaras - DVR View",
                    style={'color': 'white', 'textAlign': 'center', 'fontSize': '24px'}
                ),

                # Iframe con el HTML incrustado
                html.Iframe(
                    srcDoc=html_content,
                    style={"width": "100%", "height": "70vh", "border": "none"},
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

    return "Seleccione una pestaña para ver el contenido."





# --------------------------------------------------------------------------------------
# Callback para (opcional) actualizar frames si usaras 4 salidas (no se usa ahora)
# --------------------------------------------------------------------------------------
@app.callback(
    [Output("video-feed-1", "src"),
     Output("videoCanvas", "children"),
     Output("video-feed-3", "src"),
     Output("video-feed-4", "src")],
    [Input("interval", "n_intervals"), Input("tabs", "active_tab")]
)
def update_frame(_, active_tab):
    # Como ahora usamos un Iframe para la sección “cámaras”, podríamos no usar esto.
    if active_tab != "camaras":
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    global latest_frame
    if latest_frame:
        src_value = f"data:image/jpeg;base64,{latest_frame}"
        return src_value, None, src_value, src_value
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# ------------------------------------------------------------
# Callbacks para abrir/cerrar el Modal de "Registrar Usuario"
# ------------------------------------------------------------
@app.callback(
    Output("modal-user-registration", "is_open"),
    [Input("open-user-modal", "n_clicks")],
    [State("modal-user-registration", "is_open")]
)
def toggle_user_registration_modal(n_clicks_open, is_open):
    if n_clicks_open:
        return not is_open
    return is_open


# ------------------------------------------------------------
# Callback para el guardado del nuevo usuario
# ------------------------------------------------------------
@app.callback(
    Output("reg-user-msg", "children"),
    [Input("btn-save-user", "n_clicks")],
    [
        State("reg-nombre", "value"),
        State("reg-usuario", "value"),
        State("reg-password", "value"),
        State("reg-password2", "value")
    ]
)
def save_new_user(n_clicks, nombre, usuario, pass1, pass2):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    # Validaciones mínimas
    if not nombre or not usuario or not pass1 or not pass2:
        return dbc.Alert("Todos los campos son obligatorios.", color="warning")
    if pass1 != pass2:
        return dbc.Alert("Las contraseñas no coinciden.", color="danger")

    # Llamar al backend
    payload = {
        "nombre": nombre,
        "usuario": usuario,
        "password": pass1
    }
    try:
        response = requests.post("http://127.0.0.1:5000/register_user", json=payload)
        if response.status_code == 200:
            # Éxito
            return dbc.Alert("Usuario registrado exitosamente.", color="success")
        else:
            # Error devuelto por el backend
            msg = response.json().get("error", f"Error {response.status_code}")
            return dbc.Alert(f"Ocurrió un error: {msg}", color="danger")
    except Exception as e:
        return dbc.Alert(f"No se pudo conectar: {str(e)}", color="danger")


# ------------------------------------------------------------
# Callbacks para abrir/cerrar Modal de Tabla de Usuarios
# ------------------------------------------------------------
@app.callback(
    Output("modal-users-table", "is_open"),
    [Input("open-users-table-modal", "n_clicks")],
    [State("modal-users-table", "is_open")]
)
def toggle_users_table_modal(n_clicks_open, is_open):
    if n_clicks_open:
        return not is_open
    return is_open



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
    if active_tab != "registros" or not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    if image_content and name:
        image_data = image_content.split(",")[1]
        payload = {
            'name': name,
            'image': image_data
        }
        try:
            # Llama al backend para registrar la persona
            response = requests.post('http://127.0.0.1:5000/register', json=payload)
            if response.status_code == 200:
                # Después de registrar, llama al backend para obtener la lista actualizada de registros
                records_response = requests.get("http://127.0.0.1:5000/get_records")
                if records_response.status_code == 200:
                    records = records_response.json()
                    alert = dbc.Alert("Registro exitoso.", color="success", duration=3000)
                    new_name = ""
                    new_image = None
                    new_table = build_records_table(records)  # Pasa los registros aquí
                    return alert, new_name, new_image, new_table
                else:
                    return (
                        dbc.Alert("Error al obtener registros después de guardar.", color="danger"),
                        dash.no_update, dash.no_update, dash.no_update
                    )
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
    if n_clicks_open:
        return not is_open
    return is_open


# --------------------------------------------------------------------------------------
# Callback para actualizar logs y la gráfica dentro del Modal
# --------------------------------------------------------------------------------------


last_seen_detection_id = 0  # Globalmente, arriba de tu callback

@app.callback(
    [Output("modal-activity-logs", "children"),
     Output("modal-activity-graph", "figure")],
    Input("interval", "n_intervals"),
    State("tabs", "active_tab")
)
def update_activity_logs(_, active_tab):
    global last_seen_detection_id
    
    if active_tab != "camaras":
        return dash.no_update, dash.no_update  # No hace nada si estás en otra pestaña

    # Consulta al backend
    try:
        response = requests.get("http://127.0.0.1:5000/get_detections")
        if response.status_code == 200:
            detections = response.json()  # [{id, tipo, etiqueta, confianza, fecha}, ...]
        else:
            return (
                html.Div("Error al obtener detecciones del backend.", style={'color': 'red'}),
                go.Figure()
            )
    except Exception as e:
        return (
            html.Div(f"Error de conexión: {e}", style={'color': 'red'}),
            go.Figure()
        )

    if not detections:
        # No hay nada en la DB, limpias logs y figura
        return (html.Div("No hay detecciones."), go.Figure())

    # 1) Hallar el id máximo en los registros
    current_max_id = max(det["id"] for det in detections)

    # 2) Chequear si es mayor que el último id visto
    if current_max_id <= last_seen_detection_id:
        # Significa que NO hay detecciones nuevas => no actualizamos la interfaz
        raise dash.exceptions.PreventUpdate
    else:
        # Hay nuevas detecciones => actualizamos la interfaz
        last_seen_detection_id = current_max_id

    # ---- Construir la interfaz de logs (tarjetas) y la gráfica, como antes ----
    from dateutil import parser
    def format_datetime(fecha_str):
        try:
            dt = parser.parse(fecha_str)
            return dt.strftime('%d/%m/%Y %I:%M %p')  # Ej: "16/01/2025 02:05 PM"
        except:
            return fecha_str

    from collections import defaultdict
    detections_by_type = defaultdict(list)
    for det in detections:
        detections_by_type[det["tipo"]].append(det)

    logs_combined = []
    for tipo, lista_dets in detections_by_type.items():
        logs_combined.append(
            html.H5(f"Detecciones de {tipo}:", style={'fontWeight': 'bold', 'marginTop': '10px'})
        )

        cards_for_this_type = []
        for det in lista_dets:
            fecha_formateada = format_datetime(det['fecha'])
            card = html.Div(
                [
                    html.Div([
                        html.Span("ID: ", style={'fontWeight': 'bold'}),
                        html.Span(str(det['id']))
                    ]),
                    html.Div([
                        html.Span("Etiqueta: ", style={'fontWeight': 'bold'}),
                        html.Span(det['etiqueta'])
                    ]),
                    html.Div([
                        html.Span("Confianza: ", style={'fontWeight': 'bold'}),
                        html.Span(str(det['confianza']))
                    ]),
                    html.Div([
                        html.Span("Fecha: ", style={'fontWeight': 'bold'}),
                        html.Span(fecha_formateada)
                    ]),
                ],
                style={
                    'border': '1px solid #444',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'marginBottom': '10px',
                    'backgroundColor': '#2D2D2D'
                }
            )
            cards_for_this_type.append(card)

        container_for_type = html.Div(
            cards_for_this_type,
            style={
                'maxHeight': '200px',
                'overflowY': 'auto',
                'marginBottom': '20px'
            }
        )
        logs_combined.append(container_for_type)

    # Gráfica
    x_values = list(detections_by_type.keys())
    y_values = [len(detections_by_type[t]) for t in x_values]

    fig = go.Figure(data=[go.Bar(x=x_values, y=y_values)])
    fig.update_layout(
        title="Conteo de Detecciones",
        xaxis_title="Tipo de Reconocimiento",
        yaxis_title="Cantidad",
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
