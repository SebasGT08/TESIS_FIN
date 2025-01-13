from fastapi import FastAPI, WebSocket
import asyncio
from .camera_handler import pose_queue, object_queue, face_queue, event_queue
import cv2

# Inicializar FastAPI
app = FastAPI()


@app.websocket("/ws/poses")
async def pose_stream(websocket: WebSocket):
    """
    Transmite frames procesados con detección de poses a través de un WebSocket.
    """
    await websocket.accept()
    try:
        while True:
            if not pose_queue.empty():
                frame = pose_queue.get()
                _, buffer = cv2.imencode(".jpg", frame)
                await websocket.send_bytes(buffer.tobytes())
            await asyncio.sleep(0.03)
    except Exception as e:
        print(f"[ERROR] Conexión cerrada: {e}")
    finally:
        await websocket.close()

@app.websocket("/ws/objects")
async def object_stream(websocket: WebSocket):
    """
    Transmite frames procesados con detección de objetos a través de un WebSocket.
    """
    await websocket.accept()
    try:
        while True:
            if not object_queue.empty():
                frame = object_queue.get()
                _, buffer = cv2.imencode(".jpg", frame)
                await websocket.send_bytes(buffer.tobytes())
            await asyncio.sleep(0.03)
    except Exception as e:
        print(f"[ERROR] Conexión cerrada: {e}")
    finally:
        await websocket.close()

@app.websocket("/ws/faces")
async def face_stream(websocket: WebSocket):
    """
    Transmite frames procesados con detección de rostros a través de un WebSocket.
    """
    await websocket.accept()
    try:
        while True:
            if not face_queue.empty():
                frame = face_queue.get()
                _, buffer = cv2.imencode(".jpg", frame)
                await websocket.send_bytes(buffer.tobytes())
            await asyncio.sleep(0.03)
    except Exception as e:
        print(f"[ERROR] Conexión cerrada: {e}")
    finally:
        await websocket.close()

@app.websocket("/ws/events")
async def event_stream(websocket: WebSocket):
    """
    Transmite eventos críticos al frontend desde la cola de eventos.
    """
    await websocket.accept()
    try:
        while True:
            if not event_queue.empty():
                evento = event_queue.get()  # Obtener evento de la cola
                await websocket.send_json(evento)  # Enviar evento en formato JSON
            await asyncio.sleep(0.03)  # Pequeña pausa para evitar sobrecarga
    except Exception as e:
        print(f"[ERROR] Conexión cerrada: {e}")
    finally:
        await websocket.close()