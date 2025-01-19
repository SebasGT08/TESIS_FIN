import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Cambia si tienes otro usuario
            password="1234",  # Contraseña de MySQL
            database="tesis"  # Nombre de la base de datos
        )
        ensure_tables_exist(connection)
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def ensure_tables_exist(connection):
    try:
        cursor = connection.cursor()
        
        # Crear tabla para personas si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                persona VARCHAR(255) NOT NULL,
                encoding VARCHAR(255) NOT NULL,
                estado CHAR(1) DEFAULT 'A',
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla para detecciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detecciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tipo VARCHAR(50) NOT NULL,
                etiqueta VARCHAR(255) NOT NULL,
                confianza FLOAT NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Crear tabla usuarios si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                usuario VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                tipo CHAR(1) NOT NULL DEFAULT 'E', -- 'A' para admin, 'E' para empleado
                estado CHAR(1) DEFAULT 'A', -- 'A' activo por defecto
                creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


        connection.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print(f"Error al asegurar las tablas: {err}")
