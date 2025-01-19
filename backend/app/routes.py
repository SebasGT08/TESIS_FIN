import os
import io
import base64
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import face_recognition
from datetime import datetime
from .db_connection import get_db_connection  # Importar conexión
import os
import mysql.connector

# Directorio para guardar los encodings
ENCODINGS_FOLDER = os.path.abspath('registered_encodings')
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

def register_routes(app):
    @app.route('/register', methods=['POST'])
    def register_face():
        try:
            data = request.json

            # Validación de datos entrantes
            if 'name' not in data or 'image' not in data:
                return jsonify({"error": "El nombre y la imagen son requeridos."}), 400

            name = data['name']
            image_data = data['image']

            # Decodificar la imagen
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_np = np.array(image)

            # Obtener encodings
            encodings = face_recognition.face_encodings(image_np)
            if not encodings:
                return jsonify({"error": "No se detectó ningún rostro en la imagen."}), 400
            encoding = encodings[0]

            # Guardar el encoding como archivo .npy
            encoding_path = os.path.join(ENCODINGS_FOLDER, f"{name}.npy")
            os.makedirs(ENCODINGS_FOLDER, exist_ok=True)  # Crear carpeta si no existe
            np.save(encoding_path, encoding)

            # Inserción en la base de datos
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = """
                        INSERT INTO personas (persona, encoding, fecha, estado)
                        VALUES (%s, %s, %s, 'A')
                    """
                    cursor.execute(query, (name, f"{name}.npy", current_time))
                    connection.commit()
                finally:
                    cursor.close()
                    connection.close()
            else:
                return jsonify({"error": "No se pudo conectar a la base de datos."}), 500

            return jsonify({"message": "Registro exitoso."}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/get_records', methods=['GET'])
    def get_records():
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM personas ORDER BY id ASC")
                records = cursor.fetchall()
                cursor.close()
                connection.close()
                return jsonify(records), 200
            else:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/get_detections', methods=['GET'])
    def get_detections():
        """
        Devuelve las detecciones de la tabla 'detecciones'.
        """
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT id, tipo, etiqueta, confianza, fecha FROM detecciones ORDER BY id ASC")
                detections = cursor.fetchall()
                cursor.close()
                connection.close()
                return jsonify(detections), 200
            else:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/register_user', methods=['POST'])
    def register_user():
        """
        Registra un nuevo usuario en la tabla 'usuarios'.
        Espera un JSON con { "nombre": "...", "usuario": "...", "password": "..." }
        """
        data = request.json
        nombre = data.get('nombre')
        usuario = data.get('usuario')
        password = data.get('password')  # En prod. -> Usar hashing/bcrypt

        if not nombre or not usuario or not password:
            return jsonify({"error": "Faltan campos requeridos"}), 400

        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

            cursor = conn.cursor()
            insert_query = """
                INSERT INTO usuarios (nombre, usuario, password, estado)
                VALUES (%s, %s, %s, 'A')
            """
            cursor.execute(insert_query, (nombre, usuario, password))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({"message": "Usuario registrado exitosamente"}), 200

        except mysql.connector.Error as err:
            if err.errno == 1062:
                return jsonify({"error": "El usuario ya existe"}), 400
            return jsonify({"error": str(err)}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/login_user', methods=['POST'])
    def login_user():
        """
        Valida credenciales de usuario.
        Espera un JSON con { "usuario": "...", "password": "..." }
        """
        data = request.json
        usuario = data.get('usuario')
        password = data.get('password')

        if not usuario or not password:
            return jsonify({"error": "Credenciales incompletas"}), 400

        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

            cursor = conn.cursor(dictionary=True)
            select_query = """
                SELECT id, nombre, usuario, password, estado
                FROM usuarios
                WHERE usuario = %s AND estado = 'A'
                LIMIT 1
            """
            cursor.execute(select_query, (usuario,))
            user_row = cursor.fetchone()

            cursor.close()
            conn.close()

            if not user_row:
                return jsonify({"error": "Usuario no encontrado o inactivo"}), 401

            if user_row["password"] == password:
                return jsonify({
                    "message": "Login exitoso",
                    "user_id": user_row["id"],
                    "nombre": user_row["nombre"],
                    "usuario": user_row["usuario"]
                }), 200
            else:
                return jsonify({"error": "Contraseña incorrecta"}), 401

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/update_persona', methods=['PUT'])
    def update_persona():
        data = request.json
        persona_id = data.get('id')
        nombre = data.get('persona')

        if not persona_id or not nombre:
            return jsonify({"error": "Faltan campos requeridos"}), 400

        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

            cursor = conn.cursor()
            update_query = "UPDATE personas SET persona = %s WHERE id = %s"
            cursor.execute(update_query, (nombre, persona_id))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({"message": "Persona actualizada exitosamente"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/update_usuario', methods=['PUT'])
    def update_usuario():
            data = request.json
            usuario_id = data.get('id')
            nombre = data.get('nombre')
            usuario = data.get('usuario')
            password = data.get('password')
            tipo = data.get('tipo')

            if not usuario_id or not nombre or not usuario or not password or not tipo:
                return jsonify({"error": "Faltan campos requeridos"}), 400

            try:
                conn = get_db_connection()
                if not conn:
                    return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

                cursor = conn.cursor()
                update_query = """
                    UPDATE usuarios 
                    SET nombre = %s, usuario = %s, password = %s, tipo = %s 
                    WHERE id = %s
                """
                cursor.execute(update_query, (nombre, usuario, password, tipo, usuario_id))
                conn.commit()

                cursor.close()
                conn.close()

                return jsonify({"message": "Usuario actualizado exitosamente"}), 200

            except Exception as e:
                return jsonify({"error": str(e)}), 500


    @app.route('/delete_persona', methods=['DELETE'])
    def delete_persona():
        persona_id = request.json.get('id')

        if not persona_id:
            return jsonify({"error": "ID requerido"}), 400

        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

            cursor = conn.cursor()
            delete_query = "DELETE FROM personas WHERE id = %s"
            cursor.execute(delete_query, (persona_id,))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({"message": "Persona eliminada exitosamente"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/delete_usuario', methods=['DELETE'])
    def delete_usuario():
        usuario_id = request.json.get('id')

        if not usuario_id:
            return jsonify({"error": "ID requerido"}), 400

        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

            cursor = conn.cursor()
            delete_query = "DELETE FROM usuarios WHERE id = %s"
            cursor.execute(delete_query, (usuario_id,))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({"message": "Usuario eliminado exitosamente"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/change_estado', methods=['PUT'])
    def change_estado():
        data = request.json
        record_type = data.get('type')  # 'persona' o 'usuario'
        record_id = data.get('id')
        nuevo_estado = data.get('estado')  # 'A' o 'I'

        if not record_type or not record_id or not nuevo_estado:
            return jsonify({"error": "Faltan campos requeridos"}), 400

        try:
            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

            cursor = conn.cursor()
            if record_type == 'persona':
                update_query = "UPDATE personas SET estado = %s WHERE id = %s"
            elif record_type == 'usuario':
                update_query = "UPDATE usuarios SET estado = %s WHERE id = %s"
            else:
                return jsonify({"error": "Tipo de registro no válido"}), 400

            cursor.execute(update_query, (nuevo_estado, record_id))
            conn.commit()

            cursor.close()
            conn.close()

            return jsonify({"message": f"Estado actualizado a {nuevo_estado}"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    @app.route('/get_users', methods=['GET'])
    def get_users():
        """
        Devuelve la lista de usuarios de la tabla 'usuarios', incluyendo la contraseña.
        """
        try:
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("""
                   SELECT id, nombre, usuario, password, tipo, creado_en, estado
                        FROM usuarios
                        ORDER BY id ASC;

                """)
                users = cursor.fetchall()
                cursor.close()
                connection.close()
                return jsonify(users), 200
            else:
                return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
