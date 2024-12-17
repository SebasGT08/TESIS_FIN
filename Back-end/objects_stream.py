from ultralytics import YOLO
import cv2
import torch
import numpy as np
import socketio
import base64

# Inicializar el cliente SocketIO
sio = socketio.Client()

@sio.event
def connect():
    print("Conectado al servidor Flask (SocketIO)")

@sio.event
def disconnect():
    print("Desconectado del servidor Flask")

# Conectar al servidor Flask
sio.connect('http://127.0.0.1:5000')  # Cambia la URL si tu servidor Flask está en otra IP/puerto

# Configuración YOLOv8
model = YOLO('yolov8n-pose.pt')
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
model.conf = 0.25

# Captura de video
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("No se puede abrir el video")
    exit()

cv2.namedWindow('Detección de Poses con YOLOv8', cv2.WINDOW_NORMAL)

# Función para calcular ángulos
def calcular_angulo(a, b, c):
    a, b, c = a[:2], b[:2], c[:2]
    ba, bc = a - b, c - b
    cos_angle = np.dot(ba, bc) / ((np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6)
    angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
    return angle

# Función para detectar actividad
def detectar_actividad(keypoints):
    if keypoints.shape[0] < 17:
        return "Desconocido"

    hombro_izq, hombro_der = keypoints[5], keypoints[6]
    codo_izq, codo_der = keypoints[7], keypoints[8]
    muneca_izq, muneca_der = keypoints[9], keypoints[10]

    ang_codo_izq = calcular_angulo(hombro_izq, codo_izq, muneca_izq)
    ang_codo_der = calcular_angulo(hombro_der, codo_der, muneca_der)

    cerca_hombro_izq = (abs(muneca_izq[0] - hombro_izq[0]) < 50 and abs(muneca_izq[1] - hombro_izq[1]) < 50)
    cerca_hombro_der = (abs(muneca_der[0] - hombro_der[0]) < 50 and abs(muneca_der[1] - hombro_der[1]) < 50)

    if ang_codo_izq < 90 and ang_codo_der < 90 and cerca_hombro_izq and cerca_hombro_der:
        return "Pelear"
    return "Normal"

# Bucle principal
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, device=device, verbose=False)
        annotated_frame = results[0].plot()

        for result in results:
            if result.keypoints is not None:
                keypoints_all = result.keypoints.data.cpu().numpy()
                for keypoints in keypoints_all:
                    if keypoints.shape == (1, 17, 3):
                        keypoints = keypoints[0]
                    actividad = detectar_actividad(keypoints)

                    # Calcular el centro de los puntos clave
                    puntos_clave = keypoints[[5, 6, 9, 10], :2]
                    centro_x, centro_y = int(np.mean(puntos_clave[:, 0])), int(np.mean(puntos_clave[:, 1]))

                    cv2.putText(annotated_frame, actividad, (centro_x, centro_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Mostrar video local
        cv2.imshow('Detección de Poses con YOLOv8', annotated_frame)

        # Codificar frame y enviarlo a Flask
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        if buffer is not None:
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            sio.emit('video_frame', {'frame': frame_base64})

        # Salir si se presiona 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("Interrumpido manualmente")
finally:
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    sio.disconnect()
    print("Recursos liberados y SocketIO desconectado")
