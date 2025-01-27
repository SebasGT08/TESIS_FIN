import requests
from dash import html, dcc, Input, Output, State, no_update, exceptions, callback_context
import dash_bootstrap_components as dbc
from dateutil import parser
import ast
from dash.exceptions import PreventUpdate
import dash
import dash
ctx = dash.callback_context
from datetime import datetime
from collections import defaultdict
import plotly.graph_objects as go

# Importa MATCH, ALL para pattern matching
from dash.dependencies import MATCH, ALL

# Importa la app y layouts
from app import app
from layouts import login_layout, app_layout, layout_with_url, camaras_layout, estadisticas_layout
from utils import build_users_table, build_records_table

from dash_extensions import WebSocket  # Importar WebSocket para escuchar eventos en tiempo real
import json  # Para decodificar mensajes JSON del WebSocket


# ----------------------------------------------------------------------------
# 1) Layout según la ruta (login o principal)
# ----------------------------------------------------------------------------
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/app":
        return app_layout
    return login_layout

# ----------------------------------------------------------------------------
# 2) Login
# ----------------------------------------------------------------------------
@app.callback(
    [Output("url", "pathname"), Output("login-feedback", "children")],
    Input("btn-login", "n_clicks"),
    [State("login-usuario", "value"), State("login-password", "value")]
)
def handle_login(btn_login_clicks, usuario, password):
    if not btn_login_clicks:
        raise exceptions.PreventUpdate

    if not usuario or not password:
        return no_update, "Por favor ingrese usuario y contraseña."

    try:
        response = requests.post(
            "http://127.0.0.1:5000/login_user",
            json={"usuario": usuario, "password": password}
        )
        if response.status_code == 200:
            return "/app", ""
        else:
            return no_update, "Credenciales incorrectas. Inténtelo de nuevo."

    except Exception:
        return no_update, "Error al conectar con el servidor. Inténtelo más tarde."

# ----------------------------------------------------------------------------
# 3) Logout
# ----------------------------------------------------------------------------
@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def handle_logout(btn_logout_clicks):
    if not btn_logout_clicks:
        raise exceptions.PreventUpdate
    return "/login"

# ----------------------------------------------------------------------------
# 4) Tabs: "Registros" o "Cámaras"
# ----------------------------------------------------------------------------
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "registros":
        # Obtener lista de personas
        try:
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

        # Construye la tabla de registros (nombre + estado)
        records_table = build_records_table(records)

        return html.Div(
            style={'padding': '20px'},
            children=[

                dbc.Row(
                    [
                        # Columna izquierda (Upload de imagen)
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

                        # Columna derecha (datos y botones)
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
                                                    style={'marginBottom': '10px','fontSize':'18px','width':'70%','height':'50px'}
                                                ),
                                                html.Div(
                                                    [
                                                        dbc.Spinner(
                                                            html.Div(id='output-message'),
                                                            size="sm",
                                                            color="primary",
                                                            type="border",
                                                            fullscreen=False,
                                                        )
                                                    ],
                                                    style={'marginTop': '30px', 'fontSize': '16px'}
                                                ),
                                                html.Hr(),
                                                dbc.Button(
                                                    [
                                                        html.I(className="fas fa-user", style={"marginRight": "5px"}),
                                                        "Registrar Usuario"
                                                    ],
                                                    id="open-user-modal",
                                                    color="success",
                                                    style={'fontSize':'18px','width':'70%','marginTop':'10px'}
                                                ),
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
                    style={'color': 'white','textAlign': 'center','marginTop': '20px','fontSize': '24px'}
                ),
                html.Div(
                    id="records-table",
                    children=records_table,
                    style={'margin': '20px', 'textAlign': 'center'}
                ),

                # Modal "Registrar Usuario"
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

                # Modal con la tabla de Usuarios
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Lista de Usuarios")),
                        dbc.ModalBody(
                            [
                                html.Div(
                                    id='users-table-feedback',
                                    style={'marginBottom': '10px'}
                                ),
                                html.Div(
                                    id={'type': 'users-table-container', 'index': 'unique'},
                                    children=[]
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
                # -------------------------------------------------------------------
                # Modal para Editar Usuario (nombre, usuario, contraseña, tipo y estado)
                # -------------------------------------------------------------------
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Editar Usuario")),
                        dbc.ModalBody(
                            [

                                dbc.Input(id="edit-usuario-id", type="hidden"),
                                dbc.Label("Nombre Completo"),
                                dbc.Input(id="edit-usuario-name", type="text", placeholder="Nombre"),
                                dbc.Label("Usuario"),
                                dbc.Input(id="edit-usuario-username", type="text", placeholder="Usuario"),
                                dbc.Label("Contraseña"),
                                dbc.Input(id="edit-usuario-password", type="password", placeholder="Contraseña"),
                                dbc.Label("Tipo de Usuario"),
                                dcc.Dropdown(
                                    id="edit-usuario-tipo",
                                    options=[
                                        {"label": "Administrador", "value": "A"},
                                        {"label": "Empleado", "value": "E"},
                                    ],
                                    placeholder="Selecciona el tipo de usuario"
                                ),
                                dbc.Label("Estado"),
                                dcc.Dropdown(
                                    id="edit-usuario-estado",
                                    options=[
                                        {"label": "Activo (A)", "value": "A"},
                                        {"label": "Inactivo (I)", "value": "I"},
                                    ],
                                    placeholder="Selecciona el estado"
                                ),
                                html.Div(id="edit-user-feedback", style={"display": "none"})

                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Guardar", id="btn-update-usuario", color="primary")
                        ),
                    ],
                    id="modal-edit-usuario",
                    is_open=False,  # Asegúrate de que este valor está en False por defecto
                    size="md",
                    centered=True,
                ),


                # -------------------------------------------------------------------
                # Modal para Editar Persona (nombre + estado)
                # -------------------------------------------------------------------
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Editar Persona")),
                        dbc.ModalBody(
                            [
                                # Campo oculto con el ID
                                dbc.Input(id="edit-persona-id", type="hidden"),

                                dbc.Label("Nombre de la Persona", style={'fontSize': '16px'}),
                                dbc.Input(
                                    id="edit-persona-name",
                                    type="text",
                                    placeholder="Nombre",
                                    style={'marginBottom': '15px'}
                                ),

                                # Nuevo: Dropdown para Estado
                                dbc.Label("Estado", style={'fontSize': '16px'}),
                                dcc.Dropdown(
                                    id="edit-persona-estado",
                                    options=[
                                        {"label": "Activo (A)", "value": "A"},
                                        {"label": "Inactivo (I)", "value": "I"},
                                    ],
                                    placeholder="Selecciona Estado",
                                    style={'marginBottom': '15px'}
                                ),

                                html.Div(id="edit-persona-msg", style={'marginTop': '10px', 'color': 'red'})

                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Guardar", id="btn-update-persona", color="primary")
                        ),
                    ],
                    id="modal-edit-persona",
                    is_open=False,
                    size="md",
                    centered=True,
                ),
            ]
        )

    elif active_tab == "camaras":
        return camaras_layout
    
    elif active_tab == "estadisticas":
        return estadisticas_layout

    return "Seleccione una pestaña para ver el contenido."

# ----------------------------------------------------------------------------
# 5) Tabla de usuarios al abrir modal
# ----------------------------------------------------------------------------
@app.callback(
    Output({'type': 'users-table-container', 'index': 'unique'}, 'children'),
    Input("modal-users-table", "is_open"),
    Input('users-update-store', 'data'),
    prevent_initial_call=True
)
def update_users_table(is_open, update_trigger):
    if is_open:
        return build_users_table()
    else:
        raise exceptions.PreventUpdate

# ----------------------------------------------------------------------------
# 6) Mostrar/Ocultar Contraseña (Usuarios)
# ----------------------------------------------------------------------------
@app.callback(
    Output({'type': 'password-field', 'index': MATCH}, 'type'),
    Input({'type': 'toggle-password', 'index': MATCH}, 'n_clicks'),
    State({'type': 'password-field', 'index': MATCH}, 'type')
)
def toggle_password_visibility(n_clicks, current_type):
    if not n_clicks:
        raise exceptions.PreventUpdate
    return 'text' if current_type == 'password' else 'password'

# ----------------------------------------------------------------------------
# 7) Abrir/Cerrar Modal "Registrar Usuario"
# ----------------------------------------------------------------------------
@app.callback(
    Output("modal-user-registration", "is_open"),
    [Input("open-user-modal", "n_clicks")],
    [State("modal-user-registration", "is_open")]
)
def toggle_user_registration_modal(n_clicks_open, is_open):
    if n_clicks_open:
        return not is_open
    return is_open

# ----------------------------------------------------------------------------
# 8) Guardar nuevo Usuario
# ----------------------------------------------------------------------------
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
        raise exceptions.PreventUpdate

    if not nombre or not usuario or not pass1 or not pass2:
        return dbc.Alert("Todos los campos son obligatorios.", color="warning")
    if pass1 != pass2:
        return dbc.Alert("Las contraseñas no coinciden.", color="danger")

    payload = {
        "nombre": nombre,
        "usuario": usuario,
        "password": pass1
    }
    try:
        response = requests.post("http://127.0.0.1:5000/register_user", json=payload)
        if response.status_code == 200:
            return dbc.Alert("Usuario registrado exitosamente.", color="success")
        else:
            msg = response.json().get("error", f"Error {response.status_code}")
            return dbc.Alert(f"Ocurrió un error: {msg}", color="danger")
    except Exception as e:
        return dbc.Alert(f"No se pudo conectar: {str(e)}", color="danger")

# ----------------------------------------------------------------------------
# 9) Abrir/Cerrar Modal Tabla Usuarios
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# 10) Mostrar Imagen Cargada
# ----------------------------------------------------------------------------
@app.callback(
    Output('original-image', 'children'),
    Input('upload-image', 'contents'),
    State('upload-image', 'filename')
)
def display_images(content, filename):
    if content:
        return html.Img(
            src=content,
            style={'maxWidth': '100%', 'maxHeight': '100%', 'objectFit': 'contain'}
        )
    return None

# ----------------------------------------------------------------------------
# 11) Crear nuevo registro de Persona => refrescar tabla
# ----------------------------------------------------------------------------
@app.callback(
    [
        Output('output-message', 'children'),
        Output('input-name', 'value'),
        Output('upload-image', 'contents'),
        Output('records-table', 'children', allow_duplicate=True)  # Actualiza la tabla
    ],
    Input('save-button', 'n_clicks'),
    [State('upload-image', 'contents'), State('input-name', 'value'), State('tabs', 'active_tab')],
    prevent_initial_call=True
)
def enviar_datos_backend(n_clicks, image_content, name, active_tab):
    if active_tab != "registros" or not n_clicks:
        raise dash.exceptions.PreventUpdate

    if image_content and name:
        try:
            # (1) Envías al backend
            image_data = image_content.split(",")[1]
            payload = {'name': name, 'image': image_data}
            response = requests.post('http://127.0.0.1:5000/register', json=payload)

            # (2) Respuesta OK => recargas la lista de registros
            if response.status_code == 200:
                records_response = requests.get("http://127.0.0.1:5000/get_records")
                if records_response.status_code == 200:
                    records = records_response.json()
                    records_table = build_records_table(records)  # Construir la tabla nuevamente
                    alert = dbc.Alert("Registro exitoso.", color="success", duration=3000)
                    return alert, "", None, records_table
                else:
                    return dbc.Alert("Error al obtener registros.", color="danger"), no_update, no_update, no_update
            else:
                error_msg = response.json().get('error', 'Error desconocido')
                return dbc.Alert(f"Error del backend: {error_msg}", color="danger"), no_update, no_update, no_update
        except Exception as e:
            return dbc.Alert(f"Error de conexión: {e}", color="danger"), no_update, no_update, no_update
    else:
        return dbc.Alert("Por favor, carga una imagen y escribe un nombre.", color="warning"), no_update, no_update, no_update

# ----------------------------------------------------------------------------
# 12) Abrir/Cerrar Modal Actividad (Cámaras)
# ----------------------------------------------------------------------------
@app.callback(
    Output("activity-modal", "is_open"),
    Input("open-activity-modal", "n_clicks"),
    State("activity-modal", "is_open")
)
def toggle_activity_modal(n_clicks_open, is_open):
    if n_clicks_open:
        return not is_open
    return is_open

# ----------------------------------------------------------------------------
# 13) Actualizar logs de actividad (Cámaras)
# ----------------------------------------------------------------------------

@app.callback(
    [Output("alert-container", "children"), Output("alerts-store", "data")],  # Actualiza visual y datos
    Input("ws", "message"),  # Escucha mensajes del WebSocket
    State("alerts-store", "data"),  # Estado actual de las alertas almacenadas
)
def update_alerts(message, stored_alerts):
    if not message:
        print("No se recibió ningún mensaje del WebSocket.")
        return no_update, stored_alerts

    # Procesar el mensaje recibido
    try:
        data = json.loads(message["data"])  # Decodifica el mensaje JSON
        print(f"Mensaje WebSocket recibido: {data}")
    except Exception as e:
        print(f"Error procesando mensaje WebSocket: {e}")
        return no_update, stored_alerts

    # Crear alerta visual
    formatted_date = format_datetime(data["fecha"])
    alert = dbc.Alert(
        [
            html.H5("⚠ Alerta", className="alert-heading"),
            html.P(f"Motivo: {data['etiqueta']}", style={"fontWeight": "bold"}),
            html.P(f"{formatted_date}"),
        ],
        color="danger" if data["tipo"] == "objetos" else "warning",
        dismissable=True,
        duration=5000,
        style={
            "marginBottom": "10px",
            "borderLeft": "5px solid red" if data["tipo"] == "objetos" else "orange",
            "boxShadow": "0px 0px 10px rgba(255,0,0,0.5)" if data["tipo"] == "objetos" else "rgba(255,165,0,0.5)"
        }
    )

    # Actualizar alertas almacenadas
    if stored_alerts is None:
        stored_alerts = []
    stored_alerts.append(data)

    # Retornar la alerta más reciente y todas las alertas almacenadas
    return [alert], stored_alerts


# ----------------------------------------------------------------------------
# Callback para actualizar logs y gráficas al recibir eventos WebSocket - **CAMBIOS HECHOS**
# ----------------------------------------------------------------------------
@app.callback(
    [Output("modal-activity-logs", "children"), Output("modal-activity-graph", "figure")],
    Input("alerts-store", "data"),  # Usar alertas almacenadas
)
def update_activity_modal(alerts):
    if not alerts:
        return html.Div("No hay alertas recientes."), go.Figure()

    # Filtrar alertas válidas (que tengan las claves necesarias)
    valid_alerts = [alert for alert in alerts if all(key in alert for key in ["tipo", "etiqueta", "confianza", "fecha"])]

    if not valid_alerts:
        return html.Div("No hay alertas válidas."), go.Figure()

    # Crear logs
    logs = []
    counts = defaultdict(int)
    for alert in valid_alerts:
        tipo = alert["tipo"]
        counts[tipo] += 1

        logs.append(
            html.Div(
                [
                    html.Div([html.Span("Tipo: ", style={'fontWeight': 'bold'}), html.Span(alert["tipo"])]),
                    html.Div([html.Span("Etiqueta: ", style={'fontWeight': 'bold'}), html.Span(alert["etiqueta"])]),
                    html.Div([html.Span("Confianza: ", style={'fontWeight': 'bold'}), html.Span(f"{alert['confianza']:.2f}")]),
                    html.Div([html.Span("Fecha: ", style={'fontWeight': 'bold'}), html.Span(format_datetime(alert["fecha"]))]),
                ],
                style={
                    'border': '1px solid #444',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'marginBottom': '10px',
                    'backgroundColor': '#2D2D2D'
                }
            )
        )

    # Crear gráfica
    fig = go.Figure([go.Bar(x=list(counts.keys()), y=list(counts.values()))])
    fig.update_layout(
        title="Cantidad de Detecciones Recientes",
        xaxis_title="Tipo de Detección",
        yaxis_title="Cantidad",
        template="plotly_dark",
        paper_bgcolor='#2C2C2C',
        plot_bgcolor='#2C2C2C',
        font_color='white',
        height=400
    )

    return logs, fig


# ----------------------------------------------------------------------------
# Función para formatear fechas - **SIN CAMBIOS**
# ----------------------------------------------------------------------------
def format_datetime(fecha_str):
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime('%d/%m/%Y %I:%M %p')
    except ValueError:
        return fecha_str  # Devuelve la fecha original si hay un error

# ----------------------------------------------------------------------------
# 14) Único callback para EDITAR y ELIMINAR => "records-table" con allow_duplicate
# ----------------------------------------------------------------------------

@app.callback(
    Output("records-table", "children"),
    Input("records-store", "data")
)
def update_records_table(records):
    """
    Cada vez que `records-store.data` cambie, se vuelve a construir la tabla
    """
    return build_records_table(records)


@app.callback(
    [
        Output("users-update-store", "data", allow_duplicate=True),
        Output("modal-edit-usuario", "is_open"),
        Output("edit-usuario-id", "value"),
        Output("edit-usuario-name", "value"),
        Output("edit-usuario-username", "value"),
        Output("edit-usuario-password", "value"),
        Output("edit-usuario-tipo", "value"),
        Output("edit-usuario-estado", "value"),
    ],
    [
        Input({'type': 'edit-user', 'index': ALL}, 'n_clicks'),
        Input("btn-update-usuario", "n_clicks")
    ],
    [
        State({'type': 'edit-user', 'index': ALL}, 'id'),
        State("edit-usuario-id", "value"),
        State("edit-usuario-name", "value"),
        State("edit-usuario-username", "value"),
        State("edit-usuario-password", "value"),
        State("edit-usuario-tipo", "value"),
        State("edit-usuario-estado", "value"),
    ],
    prevent_initial_call=True
)
def handle_usuario_edit(edit_clicks_list, update_click,
                        edit_ids,
                        current_id_editing,
                        current_name_editing,
                        current_username_editing,
                        current_password_editing,
                        current_tipo_editing,
                        current_estado_editing):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"Triggered ID => {triggered_id}")

    is_modal_open = False
    new_edit_id = ""
    new_edit_name = ""
    new_edit_username = ""
    new_edit_password = ""
    new_edit_tipo = ""
    new_edit_estado = ""
    message = ""

    # 1) Abrir modal (botón "Editar")
    if "edit-user" in triggered_id:
        for i, n_clicks in enumerate(edit_clicks_list):
            if n_clicks and edit_ids[i] is not None:
                usuario_str_id = edit_ids[i]['index']
                print(f"Abrir modal para usuario ID: {usuario_str_id}")
                if usuario_str_id:
                    usuario_id = int(usuario_str_id)
                    response = requests.get(f"http://127.0.0.1:5000/get_one_usuario/{usuario_id}")
                    if response.status_code == 200:
                        data = response.json()
                        new_edit_id = str(data["id"])
                        new_edit_name = data["nombre"]
                        new_edit_username = data["usuario"]
                        new_edit_password = data["password"]
                        new_edit_tipo = data["tipo"]
                        new_edit_estado = data["estado"]
                        is_modal_open = True
                        print("Datos recibidos correctamente del backend.")
                    else:
                        print("Error al obtener datos del usuario del backend.")
                        message = dbc.Alert("Error al obtener datos.", color="danger")
                break

    # 2) Guardar cambios (botón "Guardar")
    elif triggered_id == "btn-update-usuario":
        if all([current_id_editing, current_name_editing, current_username_editing, 
                current_password_editing, current_tipo_editing, current_estado_editing]):
            print(f"Guardando => ID: {current_id_editing}, Nombre: {current_name_editing}")
            try:
                usuario_id = int(current_id_editing)
                payload = {
                    "id": usuario_id,
                    "nombre": current_name_editing,
                    "usuario": current_username_editing,
                    "password": current_password_editing,
                    "tipo": current_tipo_editing,
                    "estado": current_estado_editing
                }
                response = requests.put("http://127.0.0.1:5000/update_usuario", json=payload)
                if response.status_code == 200:
                    message = dbc.Alert("Usuario actualizado correctamente.", color="success")
                    is_modal_open = False
                else:
                    message = dbc.Alert(f"Error al actualizar: {response.json().get('error', 'Error desconocido')}", color="danger")
            except ValueError:
                message = dbc.Alert("ID no válido.", color="danger")
        else:
            message = dbc.Alert("Todos los campos son obligatorios.", color="warning")

    # 3) Refrescar la lista de usuarios después de actualizar
    records_response = requests.get("http://127.0.0.1:5000/get_users")
    if records_response.status_code == 200:
        records = records_response.json()
        return records, is_modal_open, new_edit_id, new_edit_name, new_edit_username, new_edit_password, new_edit_tipo, new_edit_estado
    else:
        return dash.no_update, is_modal_open, new_edit_id, new_edit_name, new_edit_username, new_edit_password, new_edit_tipo, new_edit_estado



@app.callback(
    Output("modal-users-table", "is_open"),
    Input("open-users-table-modal", "n_clicks"),
    prevent_initial_call=True
)
def toggle_users_table_modal(n_clicks_open):
    ctx = dash.callback_context

    print("Evento recibido en tabla de usuarios:", ctx.triggered)

    if ctx.triggered_id == "open-users-table-modal":
        print("Botón 'Ver Usuarios' presionado, mostrando tabla de usuarios.")
        return True

    print("El botón presionado no es 'Ver Usuarios'.")
    return False


def format_datetime(fecha_str):
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime('%d/%m/%Y %I:%M %p')
    except ValueError:
        return fecha_str  # Devuelve la fecha original si hay un error

    
@app.callback(
    [
        Output("modal-edit-persona", "is_open"),
        Output("edit-persona-id", "value"),
        Output("edit-persona-name", "value"),
        Output("edit-persona-estado", "value"),
        Output("records-store", "data"),
    ],
    [
        Input({'type': 'edit-record', 'index': ALL}, 'n_clicks'),
        Input("btn-update-persona", "n_clicks"),
    ],
    [
        State({'type': 'edit-record', 'index': ALL}, 'id'),
        State("edit-persona-id", "value"),
        State("edit-persona-name", "value"),
        State("edit-persona-estado", "value"),
    ],
    prevent_initial_call=True
)
def handle_persona_edit(edit_clicks_list, update_click,
                        edit_ids,
                        current_id_editing,
                        current_name_editing,
                        current_estado_editing):

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    is_modal_open = False
    new_edit_id, new_edit_name, new_edit_estado = "", "", ""

    # Abrir modal de edición
    if "edit-record" in triggered_id:
        for i, n_clicks in enumerate(edit_clicks_list):
            if n_clicks and edit_ids[i] is not None:
                persona_id = int(edit_ids[i]['index'])
                response = requests.get(f"http://127.0.0.1:5000/get_one_persona/{persona_id}")
                if response.status_code == 200:
                    data = response.json()
                    new_edit_id = str(data["id"])
                    new_edit_name = data["persona"]
                    new_edit_estado = data["estado"]
                    is_modal_open = True
        return is_modal_open, new_edit_id, new_edit_name, new_edit_estado, dash.no_update

    # Guardar cambios
    elif triggered_id == "btn-update-persona":
        if current_id_editing and current_name_editing and current_estado_editing:
            persona_id = int(current_id_editing)
            payload = {
                "id": persona_id,
                "persona": current_name_editing,
                "estado": current_estado_editing
            }
            response = requests.put("http://127.0.0.1:5000/update_persona", json=payload)
            if response.status_code == 200:
                is_modal_open = False
                records_response = requests.get("http://127.0.0.1:5000/get_records")
                if records_response.status_code == 200:
                    records = records_response.json()
                    return is_modal_open, "", "", "", records
    return dash.no_update, new_edit_id, new_edit_name, new_edit_estado, dash.no_update

@app.callback(
    [
        Output("delete-confirm-modal", "is_open"),
        Output("delete-message", "children"),
        Output("delete-persona-id", "value"),
        Output("records-store", "data", allow_duplicate=True),
    ],
    [
        Input({'type': 'delete-record', 'index': ALL}, 'n_clicks'),
        Input("btn-confirm-delete", "n_clicks"),
    ],
    [
        State({'type': 'delete-record', 'index': ALL}, 'id'),
        State("delete-persona-id", "value"),
    ],
    prevent_initial_call=True
)
def handle_persona_delete(delete_clicks_list, confirm_delete_click, delete_ids, delete_id):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    is_delete_modal_open = False
    delete_message = ""

    if "delete-record" in triggered_id:
        for i, n_clicks in enumerate(delete_clicks_list):
            if n_clicks and delete_ids[i] is not None:
                delete_id = delete_ids[i]['index']
                is_delete_modal_open = True
                return is_delete_modal_open, "", delete_id, dash.no_update

    elif triggered_id == "btn-confirm-delete":
        if delete_id:
            try:
                response = requests.delete("http://127.0.0.1:5000/delete_persona", json={"id": int(delete_id)})
                if response.status_code == 200:
                    delete_message = dbc.Alert("Persona eliminada correctamente.", color="success")
                    is_delete_modal_open = False
                    records_response = requests.get("http://127.0.0.1:5000/get_records")
                    if records_response.status_code == 200:
                        records = records_response.json()
                        return is_delete_modal_open, delete_message, "", records
                else:
                    delete_message = dbc.Alert("Error al eliminar la persona.", color="danger")
            except ValueError:
                delete_message = dbc.Alert("ID no válido.", color="danger")

    return dash.no_update, delete_message, delete_id, dash.no_update



# ----------------------------------------------------------------------------GRAFICOS
@app.callback(
    Output("grafico-1", "figure"),
    [Input("btn-refrescar", "n_clicks")],
    prevent_initial_call=True
)
def actualizar_grafico_poses(n_clicks):
    # Obtener datos desde la API
    try:
        response = requests.get(f"http://localhost:5000/get_detections?tipo=poses")
        if response.status_code != 200:
            raise Exception("Error al obtener los datos")
        detections = response.json()
    except Exception as e:
        print(f"Error al consultar API: {e}")
        return {}

    df = pd.DataFrame(detections)

    # Formatear las fechas
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['fecha_formateada'] = df['fecha'].dt.strftime('%d de %B de %Y, %H:%M')

    # Crear gráfico con slider de fechas
    fig = px.scatter(
        df,
        x="fecha",
        y="confianza",
        color="etiqueta",
        title="Detecciones de Poses",
        labels={"fecha": "Fecha y Hora", "confianza": "Confianza", "etiqueta": "Etiqueta"},
        hover_data={"confianza": True, "etiqueta": True, "fecha_formateada": True},
    )
    fig.update_traces(mode="markers+lines")
    fig.update_layout(
        xaxis=dict(
            title="Fecha y Hora",
            rangeslider=dict(visible=True),  # Slider de navegación
        ),
        yaxis=dict(title="Confianza"),
    )
    return fig

import pandas as pd
import plotly.express as px

@app.callback(
    Output("grafico-2", "figure"),
    [Input("btn-refrescar", "n_clicks")],
    prevent_initial_call=True
)
def actualizar_grafico_objetos(n_clicks):
    # Obtener datos desde la API
    try:
        response = requests.get(f"http://localhost:5000/get_detections?tipo=objetos")
        if response.status_code != 200:
            raise Exception("Error al obtener los datos")
        detections = response.json()
    except Exception as e:
        print(f"Error al consultar API: {e}")
        return {}

    df = pd.DataFrame(detections)

    # Formatear las fechas
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['fecha_formateada'] = df['fecha'].dt.strftime('%d de %B de %Y, %H:%M')

    # Crear gráfico con slider de fechas
    fig = px.scatter(
        df,
        x="fecha",
        y="confianza",
        color="etiqueta",
        title="Detecciones de Objetos",
        labels={"fecha": "Fecha y Hora", "confianza": "Confianza", "etiqueta": "Etiqueta"},
        hover_data={"confianza": True, "etiqueta": True, "fecha_formateada": True},
    )
    fig.update_traces(mode="markers+lines")
    fig.update_layout(
        xaxis=dict(
            title="Fecha y Hora",
            rangeslider=dict(visible=True),
        ),
        yaxis=dict(title="Confianza"),
    )
    return fig


@app.callback(
    Output("grafico-3", "figure"),
    [Input("btn-refrescar", "n_clicks")],
    prevent_initial_call=True
)
def actualizar_grafico_rostros(n_clicks):
    # Obtener datos desde la API
    try:
        response = requests.get(f"http://localhost:5000/get_detections?tipo=rostros")
        if response.status_code != 200:
            raise Exception("Error al obtener los datos")
        detections = response.json()
    except Exception as e:
        print(f"Error al consultar API: {e}")
        return {}

    df = pd.DataFrame(detections)

    # Formatear las fechas
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['fecha_formateada'] = df['fecha'].dt.strftime('%d de %B de %Y, %H:%M')

    # Crear gráfico con slider de fechas
    fig = px.scatter(
        df,
        x="fecha",
        y=[1] * len(df),  # Una detección por cada entrada
        color="etiqueta",
        title="Detecciones de Rostros",
        labels={"fecha": "Fecha y Hora", "y": "Detección", "etiqueta": "Etiqueta"},
        hover_data={"etiqueta": True, "fecha_formateada": True},
    )
    fig.update_traces(mode="markers+lines")
    fig.update_layout(
        xaxis=dict(
            title="Fecha y Hora",
            rangeslider=dict(visible=True),
        ),
        yaxis=dict(title="Detección"),
    )
    return fig
