import cv2
import time
from datetime import datetime
from .pose_detection import procesar_frame as procesar_poses
from .object_detection import procesar_objetos
from .face_detection import procesar_rostros
from .db_connection import get_db_connection

# Variables para colas compartidas
pose_queue = None
object_queue = None
face_queue = None
event_queue = None

def set_queues(p_pose_queue, p_object_queue, p_face_queue, p_event_queue):
    global pose_queue, object_queue, face_queue, event_queue
    pose_queue = p_pose_queue
    object_queue = p_object_queue
    face_queue = p_face_queue
    event_queue = p_event_queue

def guardar_eventos(eventos, tipo):
    try:
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

        # Colocar eventos en la cola de transmisión
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
    print("[INFO] Iniciando captura de frames...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
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

            # Procesar cada frame para detecciones
            for procesar, queue, tipo in [
                (procesar_poses, pose_queue, "poses"),
                (procesar_objetos, object_queue, "objetos"),
                (procesar_rostros, face_queue, "rostros")
            ]:
                processed_frame, eventos = procesar(frame)
                if not queue.full() and processed_frame is not None:
                    queue.put(processed_frame)
                if eventos:
                    guardar_eventos(eventos, tipo)

            time.sleep(0.03)  # Reducir uso de CPU
    except Exception as e:
        print(f"[ERROR] Error durante captura: {e}")
    finally:
        cap.release()
        print("[INFO] Cámara cerrada.")
