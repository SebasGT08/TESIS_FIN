from ultralytics import YOLO
import cv2
import torch
import numpy as np
import os
import face_recognition
from multiprocessing import Lock

# Configuración de modelo y dispositivo
base_dir = os.path.dirname(__file__)
model_path = os.path.abspath(os.path.join(base_dir, "../models/yolov8n-face.pt"))
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Dispositivo utilizado en face_detection: {device}")

model = YOLO(model_path).to(device)
model.conf = 0.25  # Umbral de confianza

# Directorio de encodings
ENCODINGS_FOLDER = os.path.abspath('registered_encodings')
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

# Variables globales para encodings
_encodings_loaded = False
known_encodings = []
known_names = []

def initialize_encodings():
    """
    Carga los encodings registrados desde el directorio especificado.
    """
    global _encodings_loaded, known_encodings, known_names
    if not _encodings_loaded:
        for filename in os.listdir(ENCODINGS_FOLDER):
            if filename.endswith('.npy'):
                name = os.path.splitext(filename)[0]
                encoding_path = os.path.join(ENCODINGS_FOLDER, filename)
                known_encodings.append(np.load(encoding_path))
                known_names.append(name)
        _encodings_loaded = True
        print(f"[INFO] Encodings cargados: {known_names}")

# Cargar los encodings al importar el módulo
initialize_encodings()

# Llamar explícitamente desde el proceso principal
def procesar_rostros(frame):
    """
    Detecta y procesa rostros en un frame.
    """

    global known_encodings, known_names
    # print(f"[DEBUG] Número de encodings conocidos: {len(known_encodings)}")
    # print(f"[DEBUG] Nombres conocidos: {known_names}")

    results = model.predict(source=frame, device=device, verbose=False)
    detections = results[0].boxes if results else []
    eventos = []

    for box in detections:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(frame.shape[1] - 1, x2), min(frame.shape[0] - 1, y2)

        # Extraer región del rostro
        face_roi = frame[y1:y2, x1:x2]
        face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

        try:
            # Reconocimiento facial
            face_encodings = face_recognition.face_encodings(face_rgb)
            name = "Desconocido"
            if face_encodings:
                face_encoding = face_encodings[0]
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                if matches and len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                else:
                    eventos.append({"etiqueta": "Desconocido", "confianza": 1.0})

            # Dibujar resultados
            cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        except Exception as e:
            print(f"[ERROR] Error en reconocimiento facial: {e}")
            cv2.putText(frame, "Error", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    return frame, eventos
