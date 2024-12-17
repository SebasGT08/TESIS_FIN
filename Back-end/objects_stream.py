from fastapi import FastAPI, WebSocket
import cv2
from ultralytics import YOLO
import asyncio
import socketio  # SocketIO client para conectarse al servidor Flask

# Inicializar la aplicación FastAPI
app = FastAPI()

# Cargar el modelo YOLO
model = YOLO("object-detection_v1.pt")

# Captura de video (cambiar el source si es necesario: 0 para webcam, archivo de video o dirección RTSP)
video_source = 0
cap = cv2.VideoCapture(video_source)

# Configuración de cliente SocketIO para conectarse al servidor Flask
sio = socketio.Client()
flask_server_url = "http://127.0.0.1:5000"  # URL del servidor Flask
try:
    sio.connect(flask_server_url)
    print("Conectado al servidor Flask vía SocketIO")
except Exception as e:
    print(f"Error al conectar con el servidor Flask: {e}")

@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    """
    Transmite video en tiempo real con detecciones YOLO a través de WebSocket y SocketIO.
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
            frame_bytes = buffer.tobytes()

            # Enviar el frame al WebSocket del cliente FastAPI
            await websocket.send_bytes(frame_bytes)

            # Enviar el mismo frame al servidor Flask usando SocketIO
            sio.emit("video_frame", {"frame": frame_bytes})

            # Introducir un pequeño retraso para evitar sobrecarga
            await asyncio.sleep(0.03)
    except Exception as e:
        print(f"Conexión cerrada: {e}")
    finally:
        cap.release()
        await websocket.close()
        sio.disconnect()
