# face_detect.py

from ultralytics import YOLO
import cv2
import torch
import mediapipe as mp
import numpy as np
import os
import face_recognition
import socketio
import base64

# Inicializar el cliente SocketIO
sio = socketio.Client()

@sio.event
def connect():
    print("Conectado al servidor SocketIO")

@sio.event
def disconnect():
    print("Desconectado del servidor SocketIO")

# Conectar al servidor SocketIO
sio.connect('http://127.0.0.1:5000')  # Asegúrate de que el servidor Flask esté ejecutándose en este puerto

# Cargar el modelo YOLOv8 pre-entrenado para detección de rostros
model = YOLO('yolov8n-face.pt')

# Verificar si hay una GPU disponible
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Usando dispositivo: {device}")

# Configurar el modelo para usar el dispositivo adecuado
model.to(device)

# Desactivar la visualización y guardado globalmente
model.overrides['visualize'] = False
model.overrides['show'] = False
model.overrides['save'] = False

# Configuración de MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=5,  # Número máximo de rostros a detectar
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Directorio donde están los encodings
ENCODINGS_FOLDER = 'registered_encodings'

def load_registered_faces():
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

# Iniciar la captura de video desde la cámara
cap = cv2.VideoCapture(0)
# Si deseas capturar desde un archivo de video, descomenta la línea siguiente y comenta la anterior
# cap = cv2.VideoCapture('assets/video_face.mp4')

if not cap.isOpened():
    print("No se puede abrir el video o la cámara")
    exit()

# Bucle principal
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo capturar el frame")
            break

        # Realizar detección de rostros con YOLOv8 sin mostrar ventanas adicionales
        results = model.predict(source=frame, device=device, verbose=False, save=False, show=False)
        
        # Obtener las detecciones del resultado
        detections = results[0].boxes  # Accedemos al primer resultado y sus cajas

        # Procesar cada detección
        if detections is not None and len(detections) > 0:
            for box in detections:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas de la caja

                # Asegurar que las coordenadas estén dentro de los límites de la imagen
                h, w = frame.shape[:2]
                x1 = max(0, min(x1, w - 1))
                y1 = max(0, min(y1, h - 1))
                x2 = max(0, min(x2, w - 1))
                y2 = max(0, min(y2, h - 1))

                # Extraer la región del rostro
                face_roi = frame[y1:y2, x1:x2]

                # Convertir la imagen a RGB para face_recognition
                face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)

                # Realizar reconocimiento facial
                try:
                    # Obtener el encoding del rostro detectado
                    face_encodings = face_recognition.face_encodings(face_rgb)
                    if len(face_encodings) > 0:
                        face_encoding = face_encodings[0]

                        # Comparar con los encodings conocidos
                        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                        name = "Desconocido"

                        # Usar la distancia más pequeña
                        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = known_names[best_match_index]

                        # Mostrar el nombre
                        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
                    else:
                        # No se pudo obtener el encoding
                        cv2.putText(frame, 'Desconocido', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                        print("No se pudo obtener el encoding del rostro detectado.")
                except Exception as e:
                    # Si ocurre un error en la extracción, marcar como desconocido
                    cv2.putText(frame, 'Desconocido', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    print(f"Error en extracción de encoding: {e}")

                # Procesar la región facial con MediaPipe
                face_results = face_mesh.process(face_rgb)

                # Dibujar la caja delimitadora
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                if face_results.multi_face_landmarks:
                    for facial_landmarks in face_results.multi_face_landmarks:
                        # Dibujar los puntos clave faciales
                        for idx, landmark in enumerate(facial_landmarks.landmark):
                            x = int(landmark.x * (x2 - x1)) + x1
                            y = int(landmark.y * (y2 - y1)) + y1

                            # Puedes ajustar el color y tamaño de los puntos
                            cv2.circle(frame, (x, y), 1, (0, 0, 255), -1)

        # Mostrar el frame anotado en la ventana creada
        cv2.imshow('Detección de Rostros y Rasgos Faciales', frame)

        # Codificar el frame como JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        if buffer is not None:
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            print(f"Frame codificado y enviado, tamaño: {len(frame_base64)}")
            sio.emit('video_frame', {'frame': frame_base64})
        else:
            print("Error al codificar el frame")


        # Emitir el frame vía SocketIO
        sio.emit('video_frame', {'frame': frame_base64})

        # Salir si se presiona la tecla 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Interrupción manual por el usuario.")

finally:
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    sio.disconnect()
    print("Recursos liberados y conexión SocketIO cerrada.")
