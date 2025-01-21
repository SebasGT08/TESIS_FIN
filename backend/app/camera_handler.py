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

# Historial de detecciones recientes (compartido)
detection_history = None

# Conexión persistente a la base de datos
db_connection = None
db_cursor = None


def set_queues(p_pose_queue, p_object_queue, p_face_queue, p_event_queue, p_detection_history):
    """
    Configura las colas compartidas y el historial de detecciones.
    """
    global pose_queue, object_queue, face_queue, event_queue, detection_history
    pose_queue = p_pose_queue
    object_queue = p_object_queue
    face_queue = p_face_queue
    event_queue = p_event_queue
    detection_history = p_detection_history


def init_db_connection():
    """
    Inicializa una conexión persistente a la base de datos.
    """
    global db_connection, db_cursor
    try:
        db_connection = get_db_connection()
        if db_connection:
            db_cursor = db_connection.cursor()
            print("[INFO] Conexión a la base de datos inicializada.")
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la conexión a la base de datos: {e}")


def close_db_connection():
    """
    Cierra la conexión persistente a la base de datos.
    """
    global db_connection, db_cursor
    try:
        if db_cursor:
            db_cursor.close()
        if db_connection:
            db_connection.close()
        print("[INFO] Conexión a la base de datos cerrada.")
    except Exception as e:
        print(f"[ERROR] No se pudo cerrar la conexión a la base de datos: {e}")

def guardar_eventos(eventos, tipo, tiempo_persistencia=30, min_ocurrencias=60, tiempo_maximo_sin_detectar=3):
    """
    Guarda eventos en la base de datos y en la cola solo si cumplen los criterios:
    1. No se han guardado en los últimos 'tiempo_persistencia' segundos.
    2. Han aparecido al menos 'min_ocurrencias' veces consecutivas antes de guardarse.
    3. Reinicia las ocurrencias si pasa más de 'tiempo_maximo_sin_detectar' segundos desde la última detección.
    """
    global db_connection, db_cursor
    try:
        now = time.time()

        for evento in eventos:
            etiqueta = evento['etiqueta']
            confianza = evento['confianza']
            print(f"[DEBUG] Procesando evento: {etiqueta}, confianza: {confianza}, tipo: {tipo}")

            # Si la detección está en el historial
            if etiqueta in detection_history:
                history = detection_history[etiqueta].copy()  # Copia el valor actual para modificarlo
                last_saved = history['last_saved']
                last_detected = history.get('last_detected', 0)
                occurrences = history['occurrences']
                last_detected_type = history['last_detected_type']

                # Verificar si ha pasado mucho tiempo desde la última ocurrencia
                if now - last_detected > tiempo_maximo_sin_detectar:
                    print(f"[DEBUG] Reiniciando ocurrencias para {etiqueta} por tiempo sin detectar.")
                    occurrences = 1
                elif tipo == last_detected_type:
                    occurrences += 1
                    print(f"[DEBUG] Incrementando ocurrencias para {etiqueta}: {occurrences}")
                else:
                    # Reinicia las ocurrencias si cambió el tipo de evento
                    occurrences = 1
                    print(f"[DEBUG] Reiniciando ocurrencias para {etiqueta} debido a cambio de tipo.")

                # Actualiza los valores en el historial
                history['occurrences'] = occurrences
                history['last_detected'] = now
                history['last_detected_type'] = tipo

                # Condiciones para guardar:
                if now - last_saved > tiempo_persistencia and occurrences >= min_ocurrencias:
                    print(f"[DEBUG] Cumple condiciones para guardar: {etiqueta}")
                    query = """
                        INSERT INTO detecciones (tipo, etiqueta, confianza, fecha)
                        VALUES (%s, %s, %s, NOW())
                    """
                    db_cursor.execute(query, (tipo, etiqueta, confianza))

                    # Coloca el evento en la cola
                    if not event_queue.full():
                        event_queue.put({
                            "tipo": tipo,
                            "etiqueta": etiqueta,
                            "confianza": confianza,
                            "fecha": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        print(f"[DEBUG] Evento colocado en la cola: {etiqueta}")

                    # Actualiza el tiempo de la última vez que se guardó
                    history['last_saved'] = now
                    print(f"[DEBUG] Reiniciando ocurrencias para {etiqueta} después de guardar.")
                    occurrences = 0  # Reinicia las ocurrencias después de guardar
                else:
                    print(f"[DEBUG] No cumple condiciones para guardar: {etiqueta}. "
                          f"Tiempo desde último guardado: {now - last_saved}, "
                          f"Ocurrencias: {occurrences}")

                # Escribe nuevamente en el diccionario compartido
                history['occurrences'] = occurrences
                detection_history[etiqueta] = history

            else:
                # Si es la primera vez que se detecta, inicializa el historial
                detection_history[etiqueta] = {
                    "last_saved": 0,  # Última vez que se guardó
                    "last_detected": now,  # Última vez que se detectó
                    "occurrences": 1,  # Número de ocurrencias consecutivas
                    "last_detected_type": tipo,  # Último tipo detectado
                }
                print(f"[DEBUG] Inicializando historial para {etiqueta}")

        # Realiza commit solo una vez por lote de eventos
        db_connection.commit()
        print("[DEBUG] Cambios confirmados en la base de datos.")
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el evento: {e}")



def capturar_frames():
    """
    Captura frames de la cámara y los procesa para detecciones.
    """
    print("[INFO] Iniciando captura de frames...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara.")
        return

    # Inicializar conexión a la base de datos
    init_db_connection()

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
                #(procesar_rostros, face_queue, "rostros")
            ]:
                processed_frame, eventos = procesar(frame)
                if not queue.full() and processed_frame is not None:
                    queue.put(processed_frame)
                if eventos:
                    guardar_eventos(eventos, tipo)

            time.sleep(0.01)  # Reducir uso de CPU
    except Exception as e:
        print(f"[ERROR] Error durante captura: {e}")
    finally:
        cap.release()
        close_db_connection()  # Cerrar conexión a la base de datos
        print("[INFO] Cámara cerrada.")
