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


# Directorio para guardar los encodings
ENCODINGS_FOLDER = os.path.abspath('registered_encodings')
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

def register_routes(app):
    @app.route('/register', methods=['POST'])
    def register_face():
        try:
            data = request.json
            name = data['name']
            image_data = data['image']

            if not name:
                return jsonify({"error": "El nombre es requerido."}), 400

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            image_np = np.array(image)

            encodings = face_recognition.face_encodings(image_np)
            if len(encodings) == 0:
                return jsonify({"error": "No se detectó ningún rostro en la imagen."}), 400

            encoding = encodings[0]
            encoding_path = os.path.join(ENCODINGS_FOLDER, f"{name}.npy")
            np.save(encoding_path, encoding)

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                query = """
                    INSERT INTO personas (persona, encoding, fecha)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(query, (name, f"{name}.npy", current_time))
                connection.commit()
                cursor.close()
                connection.close()

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
