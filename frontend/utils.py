# utils.py
import requests
from dash import html, dcc
import dash_bootstrap_components as dbc
from dateutil import parser

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
                                id={'type': 'edit-user', 'index': str(user["id"])},  # Asegúrate de convertir a string
                                 n_clicks=0,
                                color="warning",
                                size="sm",
                                style={'marginRight': '5px'}
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


def format_date(fecha):
    """Formatea la fecha al formato dd/mm/yyyy HH:MM AM/PM."""
    try:
        dt = parser.parse(fecha)
        return dt.strftime('%d/%m/%Y %I:%M %p')
    except:
        return fecha


def build_records_table(records):
    """
    Construye la tabla con barra de búsqueda, scroll y columna de estado.
    """
    if not records:
        return html.Div(
            "No hay registros disponibles.",
            style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
        )

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

            # ----------------------------------------------
            # CONVERTIMOS el record["id"] a string
            # ----------------------------------------------
            # Guárdalo en una variable p.e. str_id
            html.Td(
                [
                    dbc.Button(
                        "Editar",
                        id={'type': 'edit-record', 'index': str(record["id"])},  # <-- convertir a str
                        color="warning",
                        size="sm",
                        style={'marginRight': '5px'}
                    ),
                    
                ],
                style={'textAlign': 'center'}
            ),
        ]) for record in filtered_records
    ])




def create_table_body(records):
    """
    Crea el cuerpo de la tabla con los registros y botones de acción.
    """
    rows = []
    for record in records:
        rows.append(
            html.Tr([
                html.Td(record["id"]),
                html.Td(record["persona"]),
                html.Td(record["fecha"]),
                html.Td(record["estado"]),
                html.Td(
                    dbc.Button(
                        "Editar",
                        id={'type': 'edit-record', 'index': str(record["id"])},  # Convertir a string
                        color="warning",
                        n_clicks=0
                    )
                ),
            ])
        )
    return html.Tbody(rows)


def build_records_table(records):
    """
    Construye la tabla con barra de búsqueda, scroll y columna de estado.
    """
    if not records:
        return html.Div(
            "No hay registros disponibles.",
            style={'color': 'white', 'textAlign': 'center', 'fontSize': '18px'}
        )

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

    table_body = create_table_body(records)  # Crea el cuerpo de la tabla

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
                    'width': '100%'
                }
            )
        ],
        style={
            'maxHeight': '300px',
            'overflowY': 'scroll',
            'margin': '0 auto'
        }
    )
    return table


