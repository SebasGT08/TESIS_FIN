from insightface.app import FaceAnalysis
from deep_sort_realtime.deepsort_tracker import DeepSort
import cv2
import numpy as np
import base64
import time
from .db_connection import get_db_connection

# Configuración de modelo y dispositivo para InsightFace
app_insightface = FaceAnalysis(providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
app_insightface.prepare(ctx_id=0, det_size=(640, 640))  # ctx_id=0 para usar GPU

# Inicialización del tracker (DeepSORT)
tracker = DeepSort(max_age=30, nn_budget=10, embedder_gpu=True)

# Variables globales para encodings
_encodings_loaded = False
known_encodings = []
known_names = []

def initialize_encodings():
    """
    Carga los encodings registrados desde la base de datos.
    """
    global _encodings_loaded, known_encodings, known_names
    if not _encodings_loaded:
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT persona, encoding FROM personas WHERE estado = 'A'")
                for row in cursor.fetchall():
                    name, encoding_serialized = row
                    encoding = np.frombuffer(base64.b64decode(encoding_serialized), dtype=np.float32)
                    encoding = encoding / np.linalg.norm(encoding)  # Normalizar el encoding
                    known_encodings.append(encoding)
                    known_names.append(name)
                print(f"[DEBUG] Total encodings cargados: {len(known_encodings)}")
            except Exception as e:
                print(f"[ERROR] Error al cargar encodings desde la base de datos: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            print("[ERROR] No se pudo establecer la conexión con la base de datos.")
        _encodings_loaded = True
        print(f"[INFO] Encodings cargados: {known_names}")

# Cargar los encodings al importar el módulo
initialize_encodings()

def procesar_rostros(frame, prev_time, track_id_to_name):
    """
    Detecta y procesa rostros en un frame usando InsightFace, realiza el seguimiento con DeepSORT y mantiene la identificación.
    """
    global known_encodings, known_names

    # Detectar rostros y obtener embeddings
    faces = app_insightface.get(frame)

    detecciones = []  # Lista de detecciones para el tracker
    eventos = []  # Lista de eventos solo para notificar desconocidos

    for i, face in enumerate(faces):
        # Coordenadas del bounding box
        x1, y1, x2, y2 = map(int, face.bbox)
        width = x2 - x1
        height = y2 - y1
        x1, y1, width, height = max(0, x1), max(0, y1), max(0, width), max(0, height)

        # Extraer el embedding
        encoding = face.embedding
        encoding = encoding / np.linalg.norm(encoding)  # Normalizar el embedding detectado
        name = "Desconocido"  # Valor por defecto para rostros no identificados

        # Comparar con encodings conocidos
        if known_encodings:
            distances = np.linalg.norm(known_encodings - encoding, axis=1)
            min_distance_index = np.argmin(distances)

            if distances[min_distance_index] < 0.9:  # Umbral de similitud
                name = known_names[min_distance_index]

        # Validación de formato
        confianza = float(1.0)  # Asegurar que confianza sea flotante
        detection_bbox = [x1, y1, width, height]  # Formato esperado por DeepSORT

        # Agregar la detección al formato esperado por DeepSORT
        deteccion = (detection_bbox, confianza, name)
        detecciones.append(deteccion)

    # Actualizar el tracker con las detecciones
    try:
        tracks = tracker.update_tracks(detecciones, frame=frame)
    except Exception as e:
        return frame, eventos, prev_time

    # Dibujar los resultados del tracker en el frame
    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id  # ID único del tracker
        det_class = track.get_det_class()  # Clase detectada en esta iteración

        # Si el nombre actual es "Desconocido" pero se detecta un nombre conocido, actualiza el diccionario
        if track_id in track_id_to_name and track_id_to_name[track_id] == "Desconocido" and det_class != "Desconocido":
            track_id_to_name[track_id] = det_class
        elif track_id not in track_id_to_name:
            # Si el track_id no está en el diccionario, lo agregamos
            track_id_to_name[track_id] = det_class

        # Obtener el nombre final
        label = track_id_to_name.get(track_id, "Desconocido")

        # Agregar a eventos si sigue siendo desconocido
        if label == "Desconocido":
            eventos.append({"etiqueta": "Desconocido", "confianza": 1.0})

        # Dibujar en el frame
        bbox = track.to_tlbr()
        cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} (ID: {track_id})", (int(bbox[0]), int(bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
    # Calcular y mostrar FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return frame, eventos, prev_time
