import cv2
import time
from .pose_detection import procesar_frame as procesar_poses
from .object_detection import procesar_objetos
from .face_detection import procesar_rostros
from .db_connection import get_db_connection
import queue
from datetime import datetime

# Colas para compartir frames procesados
pose_queue = queue.Queue(maxsize=10)
object_queue = queue.Queue(maxsize=10)
face_queue = queue.Queue(maxsize=10)
event_queue = queue.Queue(maxsize=50)  # Cola para eventos críticos

def guardar_eventos(eventos, tipo):
    """
    Guarda eventos en la base de datos y los coloca en la cola de eventos para transmisión.
    """
    try:
        # Guardar en la base de datos
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            for evento in eventos:
                query = """
                    INSERT INTO detecciones (tipo, etiqueta, confianza, fecha)
                    VALUES (%s, %s, %s, NOW())
                """
                cursor.execute(query, (tipo, evento['etiqueta'], evento['confianza']))
                connection.commit()
            cursor.close()
            connection.close()

        # Colocar eventos en la cola para transmisión
        for evento in eventos:
            if not event_queue.full():
                event_queue.put({
                    "tipo": tipo,
                    "etiqueta": evento['etiqueta'],
                    "confianza": evento['confianza'],
                    "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el evento: {e}")

def capturar_frames():
    """
    Captura frames de la cámara, los procesa y maneja detecciones críticas.
    """
    print("[DEBUG] Iniciando captura de frames...")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Usa DirectShow como backend
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] No se pudo leer el frame.")
                time.sleep(0.1)
                continue

            # Procesar el frame para detección de poses
            pose_frame, eventos_poses = procesar_poses(frame)
            if not pose_queue.full():
                pose_queue.put(pose_frame)
            if eventos_poses:
                guardar_eventos(eventos_poses, "poses")

            # Procesar el frame para detección de objetos
            object_frame, eventos_objetos = procesar_objetos(frame)
            if not object_queue.full():
                object_queue.put(object_frame)
            if eventos_objetos:
                guardar_eventos(eventos_objetos, "objetos")

            # Procesar el frame para detección de rostros
            face_frame, eventos_rostros = procesar_rostros(frame)
            if not face_queue.full():
                face_queue.put(face_frame)
            if eventos_rostros:
                guardar_eventos(eventos_rostros, "rostros")

            # Pausa para evitar sobrecarga
            time.sleep(0.03)

    except Exception as e:
        print(f"[ERROR] Ocurrió un error durante la captura de frames: {e}")
    finally:
        cap.release()
        print("[DEBUG] Cámara cerrada.")
