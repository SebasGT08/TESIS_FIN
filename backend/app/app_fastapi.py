from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from .camera_handler import pose_queue, object_queue, face_queue, event_queue
import cv2

app = FastAPI()

async def safe_close(websocket: WebSocket):
    """
    Cierra el WebSocket de forma segura si está abierto.
    """
    if websocket.client_state.CONNECTED:
        try:
            await websocket.close()
        except Exception as e:
            print(f"[ERROR] Error al cerrar el WebSocket: {e}")


@app.websocket("/ws/poses")
async def pose_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if not pose_queue.empty():
                frame = pose_queue.get()
                _, buffer = cv2.imencode(".jpg", frame)
                await websocket.send_bytes(buffer.tobytes())
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print("[INFO] Conexión cerrada por el cliente en /ws/poses")
    except Exception as e:
        print(f"[ERROR] Error inesperado en /ws/poses: {e}")
    finally:
        await safe_close(websocket)


@app.websocket("/ws/objects")
async def object_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if not object_queue.empty():
                frame = object_queue.get()
                _, buffer = cv2.imencode(".jpg", frame)
                await websocket.send_bytes(buffer.tobytes())
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print("[INFO] Conexión cerrada por el cliente en /ws/objects")
    except Exception as e:
        print(f"[ERROR] Error inesperado en /ws/objects: {e}")
    finally:
        await safe_close(websocket)


@app.websocket("/ws/faces")
async def face_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if not face_queue.empty():
                frame = face_queue.get()
                _, buffer = cv2.imencode(".jpg", frame)
                await websocket.send_bytes(buffer.tobytes())
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print("[INFO] Conexión cerrada por el cliente en /ws/faces")
    except Exception as e:
        print(f"[ERROR] Error inesperado en /ws/faces: {e}")
    finally:
        await safe_close(websocket)


@app.websocket("/ws/events")
async def event_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if not event_queue.empty():
                evento = event_queue.get()
                await websocket.send_json(evento)
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print("[INFO] Conexión cerrada por el cliente en /ws/events")
    except Exception as e:
        print(f"[ERROR] Error inesperado en /ws/events: {e}")
    finally:
        await safe_close(websocket)
