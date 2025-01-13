from ultralytics import YOLO
import cv2
import torch
import numpy as np
import os

# Configuración del modelo YOLO
# Construye la ruta absoluta al modelo
base_dir = os.path.dirname(__file__)  # Directorio del archivo actual
model_path = os.path.abspath(os.path.join(base_dir, "../models/yolo11n-pose.pt"))
model = YOLO(model_path)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
model.conf = 0.25  # Ajusta el umbral de confianza si quieres

def calcular_angulo(a, b, c):
    a, b, c = a[:2], b[:2], c[:2]
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / ((np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))

def detectar_actividad(keypoints):
    if keypoints.shape[0] < 17:
        return "Desconocido"

    hombro_izq, hombro_der = keypoints[5], keypoints[6]
    codo_izq, codo_der = keypoints[7], keypoints[8]
    muneca_izq, muneca_der = keypoints[9], keypoints[10]

    ang_codo_izq = calcular_angulo(hombro_izq, codo_izq, muneca_izq)
    ang_codo_der = calcular_angulo(hombro_der, codo_der, muneca_der)

    cerca_hombro_izq = (
        abs(muneca_izq[0] - hombro_izq[0]) < 50 and
        abs(muneca_izq[1] - hombro_izq[1]) < 50
    )
    cerca_hombro_der = (
        abs(muneca_der[0] - hombro_der[0]) < 50 and
        abs(muneca_der[1] - hombro_der[1]) < 50
    )

    if ang_codo_izq < 90 and ang_codo_der < 90 and cerca_hombro_izq and cerca_hombro_der:
        return "Pelear"

    return "Normal"

def procesar_frame(frame):
    results = model.predict(frame, device=device, verbose=False)
    annotated_frame = results[0].plot()
    eventos = []

    for result in results:
        if result.keypoints is not None:
            keypoints_all = result.keypoints.data.cpu().numpy()
            for person_keypoints in keypoints_all:
                # Ajustar forma si viene como (1,17,3)
                if person_keypoints.shape == (1, 17, 3):
                    person_keypoints = person_keypoints[0]

                if person_keypoints.shape == (17, 3):
                    actividad = detectar_actividad(person_keypoints)

                    puntos_clave_indices = [5, 6, 9, 10, 13, 14]
                    subset_points = person_keypoints[puntos_clave_indices, :2]
                    centro_x = int(np.mean(subset_points[:, 0]))
                    centro_y = int(np.mean(subset_points[:, 1]))

                    cv2.putText(annotated_frame, actividad, (centro_x, centro_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    
                    if actividad == "Pelear":  # Evento crítico
                        eventos.append({"etiqueta": "Pelear", "confianza": 1.0})
                    

    return annotated_frame, eventos
