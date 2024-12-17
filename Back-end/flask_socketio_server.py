import os
import io
import base64
import numpy as np
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from PIL import Image
import face_recognition
from datetime import datetime
from db_connection import get_db_connection  # Importar la conexión

# Inicializar Flask y SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Directorio para guardar los encodings
ENCODINGS_FOLDER = 'registered_encodings'
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

# Endpoint HTTP para registrar un rostro
@app.route('/register', methods=['POST'])
def register_face():
    try:
        # Obtener datos del JSON
        data = request.json
        name = data['name']
        image_data = data['image']

        # Validar que se proporcionó un nombre
        if not name:
            return jsonify({"error": "El nombre es requerido."}), 400

        # Decodificar la imagen
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # Convertir la imagen a un formato compatible con face_recognition
        image_np = np.array(image)

        # Detectar y extraer el encoding facial
        encodings = face_recognition.face_encodings(image_np)
        if len(encodings) == 0:
            return jsonify({"error": "No se detectó ningún rostro en la imagen."}), 400

        encoding = encodings[0]

        # Guardar el encoding en un archivo numpy
        encoding_path = os.path.join(ENCODINGS_FOLDER, f"{name}.npy")
        np.save(encoding_path, encoding)

        # Obtener la fecha y hora actual
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Guardar los datos en MySQL
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

        # Responder con éxito
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

# Eventos WebSocket
@socketio.on('connect')
def handle_connect():
    print("Un cliente se ha conectado.")

@socketio.on('disconnect')
def handle_disconnect():
    print("Un cliente se ha desconectado.")

@socketio.on('video_frame')
def handle_video_frame(data):
    frame = data.get('frame')
    if frame:
        # Emitir el frame a todos los clientes conectados excepto al remitente
        emit('video_frame', {'frame': frame}, broadcast=True, include_self=False)

# Iniciar servidor único
if __name__ == '__main__':
    print("Servidor único con Flask y SocketIO iniciando en http://127.0.0.1:5000")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
