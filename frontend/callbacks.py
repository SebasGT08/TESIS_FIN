import requests
from dash import html, dcc, Input, Output, State, no_update, exceptions, callback_context
import dash_bootstrap_components as dbc
from dateutil import parser
import ast

# Importa MATCH, ALL para pattern matching
from dash.dependencies import MATCH, ALL

# Importa la app y layouts
from app import app
from layouts import login_layout, app_layout, layout_with_url, camaras_layout
from utils import build_users_table, build_records_table

# Variables globales (opcionales)
latest_frame = None
activity_logs_facial = []
activity_logs_objetos = []
activity_logs_poses = []
detection_count_facial = 0
detection_count_objetos = 0
detection_count_poses = 0

last_seen_detection_id = 0  # Para detecciones en la tab "cámaras"

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

        records_table = build_records_table(records)

        return html.Div(
            style={'padding': '20px'},
            children=[
                dbc.Row(
                    [
                        # Col izquierda (Upload)
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

                        # Col derecha (datos y botones)
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

                # Modal para Editar Persona
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Editar Nombre de la Persona")),
                        dbc.ModalBody(
                            [
                                dbc.Input(id="edit-persona-id", type="hidden"),
                                dbc.Label("Nombre de la Persona", style={'fontSize': '16px'}),
                                dbc.Input(
                                    id="edit-persona-name",
                                    type="text",
                                    placeholder="Nombre",
                                    style={'marginBottom': '15px'}
                                ),
                                html.Div(id="edit-persona-msg", style={'marginTop':'10px', 'color': 'red'})
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
@app.callback(
    Output("modal-users-table", "is_open"),
    [Input("open-users-table-modal", "n_clicks")],
    [State("modal-users-table", "is_open")]
)
def toggle_users_table_modal(n_clicks_open, is_open):
    if n_clicks_open:
        return not is_open
    return is_open

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
        # DEVOLVEMOS A records-table.children con allow_duplicate
        Output('records-table', 'children', allow_duplicate=True),
    ],
    Input('save-button', 'n_clicks'),
    [State('upload-image', 'contents'), State('input-name', 'value'), State('tabs', 'active_tab')],
    prevent_initial_call=True  # NECESARIO para allow_duplicate
)
def enviar_datos_backend(n_clicks, image_content, name, active_tab):
    if active_tab != "registros" or not n_clicks:
        return no_update, no_update, no_update, no_update

    if image_content and name:
        image_data = image_content.split(",")[1]
        payload = {
            'name': name,
            'image': image_data
        }
        try:
            response = requests.post('http://127.0.0.1:5000/register', json=payload)
            if response.status_code == 200:
                # Refrescar la tabla
                records_response = requests.get("http://127.0.0.1:5000/get_records")
                if records_response.status_code == 200:
                    records = records_response.json()
                    alert = dbc.Alert("Registro exitoso.", color="success", duration=3000)
                    new_table = build_records_table(records)
                    return alert, "", None, new_table
                else:
                    return (
                        dbc.Alert("Error al obtener registros después de guardar.", color="danger"),
                        no_update, no_update, no_update
                    )
            else:
                error_msg = response.json().get('error', 'Error desconocido')
                return dbc.Alert(f"Error del backend: {error_msg}", color="danger"), no_update, no_update, no_update
        except Exception as e:
            return dbc.Alert(f"Error de conexión con el backend: {e}", color="danger"), no_update, no_update, no_update
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
    [
        Output("modal-activity-logs", "children"),
        Output("modal-activity-graph", "figure")
    ],
    Input("interval", "n_intervals"),
    State("tabs", "active_tab")
)
def update_activity_logs(_, active_tab):
    global last_seen_detection_id

    if active_tab != "camaras":
        return no_update, no_update

    try:
        response = requests.get("http://127.0.0.1:5000/get_detections")
        if response.status_code == 200:
            detections = response.json()
        else:
            return html.Div("Error al obtener detecciones del backend.", style={'color': 'red'}), {}
    except Exception as e:
        return html.Div(f"Error de conexión: {e}", style={'color': 'red'}), {}

    if not detections:
        return html.Div("No hay detecciones."), {}

    current_max_id = max(det["id"] for det in detections)
    if current_max_id <= last_seen_detection_id:
        raise exceptions.PreventUpdate
    else:
        last_seen_detection_id = current_max_id

    from collections import defaultdict
    detections_by_type = defaultdict(list)
    for det in detections:
        detections_by_type[det["tipo"]].append(det)

    def format_datetime(fecha_str):
        try:
            dt = parser.parse(fecha_str)
            return dt.strftime('%d/%m/%Y %I:%M %p')
        except:
            return fecha_str

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

    import plotly.graph_objects as go
    x_values = list(detections_by_type.keys())
    y_values = [len(detections_by_type[t]) for t in x_values]

    fig = go.Figure([go.Bar(x=x_values, y=y_values)])
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

# ----------------------------------------------------------------------------
# 14) Único callback para EDITAR y ELIMINAR => "records-table" con allow_duplicate
# ----------------------------------------------------------------------------
@app.callback(
    [
        Output("records-table", "children", allow_duplicate=True),
        Output("modal-edit-persona", "is_open"),
        Output("edit-persona-id", "value"),
        Output("edit-persona-name", "value"),
    ],
    [
        Input({'type': 'confirm-delete-provider-record', 'index': ALL}, 'submit_n_clicks'),
        Input({'type': 'edit-record', 'index': ALL}, 'n_clicks'),
        Input("btn-update-persona", "n_clicks"),
    ],
    [
        State({'type': 'confirm-delete-provider-record', 'index': ALL}, 'index'),
        State({'type': 'edit-record', 'index': ALL}, 'index'),
        State("edit-persona-id", "value"),
        State("edit-persona-name", "value"),
    ],
    prevent_initial_call=True
)
def handle_persona_actions(
    delete_clicks_list,
    edit_clicks_list,
    update_click,
    delete_ids,
    edit_ids,
    current_id_editing,
    current_name_editing
):
    ctx = callback_context
    if not ctx.triggered:
        raise exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    is_modal_open = False
    new_edit_id = ""
    new_edit_name = ""

    # ELIMINAR
    if "confirm-delete-provider-record" in triggered_id:
        for i, n_clicks in enumerate(delete_clicks_list):
            if n_clicks:
                persona_str_id = delete_ids[i]
                print("persona_str_id =>", persona_str_id)
                
                # Evitar int(None)
                if persona_str_id is None:
                    print("ERROR: Este registro no tiene ID (None).")
                    break

                try:
                    persona_id = int(persona_str_id)
                except ValueError:
                    print("ERROR: No se puede convertir a int:", persona_str_id)
                    break

                print("Eliminando persona_id =>", persona_id)
                requests.delete(
                    "http://127.0.0.1:5000/delete_persona",
                    json={"id": persona_id},
                    headers={"Content-Type":"application/json"}
                )
                break

    # EDITAR (Abrir modal)
    elif "edit-record" in triggered_id:
        for i, n_clicks in enumerate(edit_clicks_list):
            if n_clicks:
                persona_str_id = edit_ids[i]
                print("Abriendo modal para persona_str_id =>", persona_str_id)

                if persona_str_id is None:
                    print("ERROR: Persona con ID None, no se abre modal.")
                    break

                # Almacenas en string. Convertirás a int al GUARDAR, si deseas
                is_modal_open = True
                new_edit_id = persona_str_id
                new_edit_name = ""
                break

    # GUARDAR
    elif triggered_id == "btn-update-persona":
        if current_id_editing and current_name_editing:
            print("Guardando cambios =>", current_id_editing, current_name_editing)

            # Evitar int(None)
            if current_id_editing is None:
                print("ERROR: current_id_editing es None.")
                raise exceptions.PreventUpdate

            try:
                persona_id = int(current_id_editing)
            except ValueError:
                print("ERROR: No se pudo convertir a int:", current_id_editing)
                raise exceptions.PreventUpdate

            payload = {'id': persona_id, 'persona': current_name_editing}
            requests.put(
                "http://127.0.0.1:5000/update_persona",
                json=payload,
                headers={"Content-Type":"application/json"}
            )
        # Cierra modal
        is_modal_open = False

    records_response = requests.get("http://127.0.0.1:5000/get_records")
    if records_response.status_code == 200:
        records = records_response.json()
        updated_table = build_records_table(records)
        return updated_table, is_modal_open, new_edit_id, new_edit_name
    else:
        return no_update, no_update, no_update, no_update
