import cv2
import time
from .pose_detection import procesar_frame as procesar_poses
from .object_detection import procesar_objetos
from .face_detection import procesar_rostros
import queue

# Colas para compartir frames procesados
pose_queue = queue.Queue(maxsize=10)
object_queue = queue.Queue(maxsize=10)
face_queue = queue.Queue(maxsize=10) 

def capturar_frames():
    """
    Captura frames de la cámara, los procesa y los coloca en las colas correspondientes.
    """
    print("[DEBUG] Iniciando captura de frames...")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Usa DirectShow como backend
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara.")
        return

    print("[DEBUG] Cámara abierta. Comenzando a leer frames...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] No se pudo leer el frame.")
                time.sleep(0.1)
                continue

            # Procesar el frame para detección de poses
            pose_frame = procesar_poses(frame)
            if not pose_queue.full():
                pose_queue.put(pose_frame)

            # Procesar el frame para detección de objetos
            object_frame = procesar_objetos(frame)
            if not object_queue.full():
                object_queue.put(object_frame)

            # Procesar el frame para detección de rostros
            face_frame = procesar_rostros(frame)
            if not face_queue.full():
                face_queue.put(face_frame)


            # Pausa para evitar sobrecarga
            time.sleep(0.03)

    except Exception as e:
        print(f"[ERROR] Ocurrió un error durante la captura de frames: {e}")
    finally:
        cap.release()
        print("[DEBUG] Cámara cerrada.")
