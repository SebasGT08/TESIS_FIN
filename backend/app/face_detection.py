from ultralytics import YOLO
import cv2
import torch
# import mediapipe as mp
import numpy as np
import os
import face_recognition

# Construye la ruta absoluta al modelo
base_dir = os.path.dirname(__file__)  # Directorio del archivo actual
model_path = os.path.abspath(os.path.join(base_dir, "../models/yolov8n-face.pt"))
model = YOLO(model_path)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
model.conf = 0.25  # Ajusta el umbral de confianza

# Configuración de MediaPipe Face Mesh
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     static_image_mode=False,
#     max_num_faces=5,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

# Directorio donde están los encodings registrados
ENCODINGS_FOLDER = os.path.abspath('registered_encodings')
os.makedirs(ENCODINGS_FOLDER, exist_ok=True)

def load_registered_faces():
    """
    Carga los encodings registrados desde el directorio especificado.
    """
    known_encodings = []
    known_names = []
    for filename in os.listdir(ENCODINGS_FOLDER):
        if filename.endswith('.npy'):
            name = os.path.splitext(filename)[0]
            encoding_path = os.path.join(ENCODINGS_FOLDER, filename)
            encoding = np.load(encoding_path)
            known_encodings.append(encoding)
            known_names.append(name)
    return known_encodings, known_names

# Cargar los encodings al iniciar
known_encodings, known_names = load_registered_faces()
print(f"Encodings cargados: {known_names}")

def procesar_rostros(frame):
    """
    Procesa un frame para detectar rostros, realiza reconocimiento facial y anota los resultados.
    """
    # Realizar detección de rostros con YOLO
    results = model.predict(source=frame, device=device, verbose=False)
    detections = results[0].boxes
    eventos = []

    if detections is not None and len(detections) > 0:
        for box in detections:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas de la caja
            h, w = frame.shape[:2]
            x1 = max(0, min(x1, w - 1))
            y1 = max(0, min(y1, h - 1))
            x2 = max(0, min(x2, w - 1))
            y2 = max(0, min(y2, h - 1))

            # Extraer la región del rostro
            face_roi = frame[y1:y2, x1:x2]
            face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

            # Reconocimiento facial
            try:
                face_encodings = face_recognition.face_encodings(face_rgb)
                name = "Desconocido"
                if len(face_encodings) > 0:
                    face_encoding = face_encodings[0]
                    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_names[best_match_index]
                        if not any(matches):  # Rostro no reconocido
                            eventos.append({"etiqueta": "Desconocido", "confianza": 1.0})

                # Dibujar el nombre y la caja alrededor del rostro
                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            except Exception as e:
                # Si ocurre un error, anotar como desconocido
                cv2.putText(frame, "Desconocido", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                print(f"Error en reconocimiento facial: {e}")

            # Procesar puntos clave faciales con MediaPipe
            # face_results = face_mesh.process(face_rgb)
            # if face_results.multi_face_landmarks:
            #     for facial_landmarks in face_results.multi_face_landmarks:
            #         for landmark in facial_landmarks.landmark:
            #             x = int(landmark.x * (x2 - x1)) + x1
            #             y = int(landmark.y * (y2 - y1)) + y1
            #             cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

    return frame, eventos
