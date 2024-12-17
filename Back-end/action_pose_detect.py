from ultralytics import YOLO
import cv2
import torch
import numpy as np
import socketio  # Cliente SocketIO

# Modelo YOLOv8 para detección de poses
model = YOLO('yolov8n-pose.pt')
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
model.conf = 0.25

# Configuración de SocketIO
sio = socketio.Client()
server_url = "http://127.0.0.1:5000"  # URL del servidor Flask
sio.connect(server_url)

# Captura de video
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("No se puede abrir el video")
    exit()

cv2.namedWindow('Detección de Poses con YOLOv8', cv2.WINDOW_NORMAL)

# Función para calcular ángulos
def calcular_angulo(a, b, c):
    a = a[:2]
    b = b[:2]
    c = c[:2]
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / ((np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))
    return angle

# Función para detectar actividad
def detectar_actividad(keypoints):
    if keypoints.shape[0] < 17:
        return "Desconocido"

    hombro_izq = keypoints[5]
    hombro_der = keypoints[6]
    codo_izq = keypoints[7]
    codo_der = keypoints[8]
    muneca_izq = keypoints[9]
    muneca_der = keypoints[10]
    cadera_izq = keypoints[11]
    cadera_der = keypoints[12]
    rodilla_izq = keypoints[13]
    rodilla_der = keypoints[14]
    tobillo_izq = keypoints[15]
    tobillo_der = keypoints[16]

    ang_codo_izq = calcular_angulo(hombro_izq, codo_izq, muneca_izq)
    ang_codo_der = calcular_angulo(hombro_der, codo_der, muneca_der)

    cerca_hombro_izq = (abs(muneca_izq[0] - hombro_izq[0]) < 50 and abs(muneca_izq[1] - hombro_izq[1]) < 50)
    cerca_hombro_der = (abs(muneca_der[0] - hombro_der[0]) < 50 and abs(muneca_der[1] - hombro_der[1]) < 50)

    if ang_codo_izq < 90 and ang_codo_der < 90 and cerca_hombro_izq and cerca_hombro_der:
        return "Pelear"

    puntos_cuerpo = np.array([hombro_izq[:2], hombro_der[:2], cadera_izq[:2], cadera_der[:2],
                              rodilla_izq[:2], rodilla_der[:2], tobillo_izq[:2], tobillo_der[:2]])
    max_y = np.max(puntos_cuerpo[:, 1])
    min_y = np.min(puntos_cuerpo[:, 1])
    hombros_y_mean = (hombro_izq[1] + hombro_der[1]) / 2
    if (max_y - min_y < 50) and (hombros_y_mean > 400):
        return "Acostado"

    if (muneca_izq[1] < hombro_izq[1] and muneca_der[1] < hombro_der[1]):
        if (rodilla_izq[1] < cadera_izq[1] and rodilla_der[1] < cadera_der[1]):
            return "Trepar"

    return "Normal"

# Evento de conexión
@sio.event
def connect():
    print("Conectado al servidor SocketIO")

# Evento de desconexión
@sio.event
def disconnect():
    print("Desconectado del servidor")

# Procesamiento del video
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame, device=device, verbose=False)
    annotated_frame = results[0].plot()

    for idx, result in enumerate(results):
        if result.keypoints is not None:
            keypoints_all = result.keypoints.data.cpu().numpy()

            for i, person_keypoints in enumerate(keypoints_all):
                if person_keypoints.shape == (1, 17, 3):
                    person_keypoints = person_keypoints[0]

                if person_keypoints.shape == (17, 3):
                    actividad = detectar_actividad(person_keypoints)

                    puntos_clave_indices = [5, 6, 9, 10, 13, 14]
                    subset_points = person_keypoints[puntos_clave_indices, :2]
                    centro_x = int(np.mean(subset_points[:, 0]))
                    centro_y = int(np.mean(subset_points[:, 1]))

                    cv2.putText(annotated_frame, actividad, (centro_x, centro_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                else:
                    cv2.putText(annotated_frame, "Desconocido", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Enviar el frame al servidor
    _, buffer = cv2.imencode('.jpg', annotated_frame)
    encoded_frame = buffer.tobytes()
    sio.emit('video_frame', {'frame': encoded_frame})

    # Mostrar el video local
    cv2.imshow('Detección de Poses con YOLOv8', annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
sio.disconnect()
