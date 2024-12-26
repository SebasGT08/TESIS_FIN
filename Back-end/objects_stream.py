from fastapi import FastAPI, WebSocket
import cv2
from ultralytics import YOLO
import asyncio

# Inicializar la aplicación FastAPI
app = FastAPI()

# Cargar el modelo YOLO
model = YOLO("object-detection_v1.pt")

# Captura de video (cambiar el source si es necesario: 0 para webcam, archivo de video o dirección RTSP)
video_source = 0  # Aquí estás usando "source=2"
cap = cv2.VideoCapture(video_source)

@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    """
    Transmite video en tiempo real con detecciones YOLO.
    """
    await websocket.accept()
    try:
        while True:
            # Leer un frame del video
            ret, frame = cap.read()
            if not ret:
                break

            # Realizar detección con YOLO
            results = model.predict(frame, show=False)
            annotated_frame = results[0].plot()  # Renderizar las detecciones en el frame

            # Codificar el frame procesado a formato JPEG
            _, buffer = cv2.imencode(".jpg", annotated_frame)

            # Enviar el frame a través del WebSocket
            await websocket.send_bytes(buffer.tobytes())

            # Introducir un pequeño retraso para evitar sobrecarga
            await asyncio.sleep(0.03)
    except Exception as e:
        print(f"Conexión cerrada: {e}")
    finally:
        cap.release()
        await websocket.close()  