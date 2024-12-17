from flask import Flask, request, jsonify
import base64
from PIL import Image
import io
import os
import numpy as np
import face_recognition

app = Flask(__name__)

# Directorio para guardar los encodings
ENCODINGS_FOLDER = 'registered_encodings'
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

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

        # Responder con éxito
        return jsonify({"message": "Registro exitoso."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
