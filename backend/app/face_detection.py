from insightface.app import FaceAnalysis
import cv2
import numpy as np
import os
import base64
import mysql.connector
import time
from multiprocessing import Lock
from .db_connection import get_db_connection

# Configuración de modelo y dispositivo para InsightFace
app_insightface = FaceAnalysis(providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
app_insightface.prepare(ctx_id=0, det_size=(640, 640))  # ctx_id=0 para usar GPU

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

def procesar_rostros(frame, prev_time):
    """
    Detecta y procesa rostros en un frame usando InsightFace y calcula los FPS.
    """

    global known_encodings, known_names

    # Detectar rostros y obtener embeddings
    # print("[DEBUG] Procesando frame para detección de rostros.")
    faces = app_insightface.get(frame)
    # print(f"[DEBUG] Rostros detectados: {len(faces)}")
    eventos = []

    for i, face in enumerate(faces):
        # print(f"[DEBUG] Procesando rostro {i + 1} de {len(faces)}")
        x1, y1, x2, y2 = map(int, face.bbox)
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(frame.shape[1] - 1, x2), min(frame.shape[0] - 1, y2)
        # print(f"[DEBUG] Coordenadas del rostro: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

        # Extraer el embedding
        encoding = face.embedding
        encoding = encoding / np.linalg.norm(encoding)  # Normalizar el embedding detectado
        name = "Desconocido"

        # Comparar con encodings conocidos
        if known_encodings:
            distances = np.linalg.norm(known_encodings - encoding, axis=1)
            min_distance_index = np.argmin(distances)

            if distances[min_distance_index] < 0.8:  # Umbral de similitud
                name = known_names[min_distance_index]
                # print(f"[DEBUG] Rostro reconocido como: {name} (distancia={distances[min_distance_index]})")
            else:
                # print(f"[DEBUG] Rostro desconocido (distancia mínima={distances[min_distance_index]})")
                eventos.append({"etiqueta": "Desconocido", "confianza": 1.0})

        # Dibujar resultados
        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Calcular y mostrar FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return frame, eventos, prev_time


