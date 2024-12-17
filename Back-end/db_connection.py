import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Cambia si tienes otro usuario
            password="1234",  # Contraseña de MySQL
            database="tesis"  # Nombre de la base de datos
        )
        ensure_table_exists(connection)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def ensure_table_exists(connection):
    try:
        cursor = connection.cursor()
        # Verificar si la tabla existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                persona VARCHAR(255) NOT NULL,
                encoding VARCHAR(255) NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error al asegurar la tabla: {err}")
