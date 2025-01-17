from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import cv2

# Variables globales para las colas
pose_queue = None
object_queue = None
face_queue = None
event_queue = None

def set_queues(p_pose_queue, p_object_queue, p_face_queue, p_event_queue):
    """
    Asigna las colas compartidas desde el proceso principal.
    """
    global pose_queue, object_queue, face_queue, event_queue
    pose_queue = p_pose_queue
    object_queue = p_object_queue
    face_queue = p_face_queue
    event_queue = p_event_queue

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
    print("[DEBUG] Cliente conectado a /ws/poses")
    try:
        while True:
            if pose_queue and not pose_queue.empty():
                frame = pose_queue.get()
                if frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame)
                    if _:
                        await websocket.send_bytes(buffer.tobytes())
                        # print("[DEBUG] Frame de poses enviado al cliente.")
                    else:
                        print("[ERROR] Falló la codificación del frame de poses.")
            else:
                print("[DEBUG] Cola de poses vacía.")
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
    print("[DEBUG] Cliente conectado a /ws/objects")
    try:
        while True:
            if object_queue and not object_queue.empty():
                frame = object_queue.get()
                if frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame)
                    if _:
                        await websocket.send_bytes(buffer.tobytes())
                        # print("[DEBUG] Frame de objetos enviado al cliente.")
                    else:
                        print("[ERROR] Falló la codificación del frame de objetos.")
            else:
                print("[DEBUG] Cola de objetos vacía.")
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
    print("[DEBUG] Cliente conectado a /ws/faces")
    try:
        while True:
            if face_queue and not face_queue.empty():
                frame = face_queue.get()
                if frame is not None:
                    _, buffer = cv2.imencode(".jpg", frame)
                    if _:
                        await websocket.send_bytes(buffer.tobytes())
                        # print("[DEBUG] Frame de rostros enviado al cliente.")
                    else:
                        print("[ERROR] Falló la codificación del frame de rostros.")
            else:
                print("[DEBUG] Cola de rostros vacía.")
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
    print("[DEBUG] Cliente conectado a /ws/events")
    try:
        while True:
            if event_queue and not event_queue.empty():
                evento = event_queue.get()
                if evento is not None:
                    await websocket.send_json(evento)
                    # print("[DEBUG] Evento enviado al cliente.")
            else:
                print("[DEBUG] Cola de eventos vacía.")
            await asyncio.sleep(0.03)
    except WebSocketDisconnect:
        print("[INFO] Conexión cerrada por el cliente en /ws/events")
    except Exception as e:
        print(f"[ERROR] Error inesperado en /ws/events: {e}")
    finally:
        await safe_close(websocket)
