import os
import cv2
import torch
import numpy as np
from ultralytics import YOLO

# ---------------------------------------------------
# 1. Configuración del modelo YOLO
# ---------------------------------------------------
base_dir = os.path.dirname(__file__)  # Directorio del archivo actual
model_path = os.path.abspath(os.path.join(base_dir, "../models/yolo11n-pose.pt"))

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = YOLO(model_path).to(device)
model.conf = 0.25  # Ajusta el umbral de confianza si lo consideras necesario

# ---------------------------------------------------
# 2. Funciones auxiliares
# ---------------------------------------------------
def calcular_angulo(a, b, c):
    """
    Calcula el ángulo (en grados) entre los vectores BA y BC.
    'a', 'b' y 'c' son arrays (x, y, conf).
    """
    a, b, c = a[:2], b[:2], c[:2]
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / ((np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))

def distancia(a, b):
    """
    Calcula la distancia euclidiana entre dos puntos 2D (x1, y1) y (x2, y2).
    """
    return np.linalg.norm(a[:2] - b[:2])

def bounding_box_persona(keypoints):
    """
    Devuelve la bounding box [xmin, ymin, xmax, ymax] basada en los keypoints.
    """
    xs = keypoints[:, 0]
    ys = keypoints[:, 1]
    return [np.min(xs), np.min(ys), np.max(xs), np.max(ys)]

def keypoint_valido(kp):
    """
    Verifica si un keypoint tiene coordenadas y confianza > 0.
    Ajusta la lógica según cómo vengan tus datos.
    """
    if kp is None or len(kp) < 3:
        return False
    x, y, conf = kp
    return conf > 0.0

def get_kp(keypoints, idx):
    """
    Retorna el keypoint en keypoints[idx] si es válido, o None si está fuera
    de rango o la confianza es 0.
    """
    if idx < 0 or idx >= len(keypoints):
        return None
    kp = keypoints[idx]
    return kp if keypoint_valido(kp) else None

# ---------------------------------------------------
# 3. Lógica de detección de actividad
# ---------------------------------------------------
def detectar_actividad(keypoints):
    """
    Devuelve la etiqueta de la actividad detectada:
        - Pelear
        - Trepar
        - Acostado
        - Normal (por defecto o si faltan keypoints o no coincide ninguna acción)

    Indices COCO:
      0: Nariz
      1: Ojo izq   2: Ojo der
      3: Oreja izq 4: Oreja der
      5: Hombro izq,  6: Hombro der
      7: Codo izq,    8: Codo der
      9: Muñeca izq, 10: Muñeca der
      11: Cadera izq, 12: Cadera der
      13: Rodilla izq,14: Rodilla der
      15: Tobillo izq,16: Tobillo der
    """

    CONFIDENCE_THRESHOLD = 0.5

    # Si no hay al menos 17 keypoints, lo consideramos "Normal"
    if keypoints.shape[0] < 17:
        return "Normal"

    # Filtrar keypoints por confianza
    def filtrar_kp(kp):
        return kp if kp is not None and kp[2] >= CONFIDENCE_THRESHOLD else None

    # Diccionario para obtener y filtrar keypoints rápidamente
    indices = {
        'nariz': 0, 'ojo_izq': 1, 'ojo_der': 2,
        'hombro_izq': 5, 'hombro_der': 6,
        'codo_izq': 7, 'codo_der': 8,
        'muneca_izq': 9, 'muneca_der': 10,
        'cadera_izq': 11, 'cadera_der': 12
    }

    keypoints_validos = {}
    for nombre, idx in indices.items():
        kp_bruto = get_kp(keypoints, idx)
        keypoints_validos[nombre] = filtrar_kp(kp_bruto)

    # ----------------------------------------------
    # Verificar que haya keypoints mínimos
    # (nariz y hombros) para cualquier acción
    # ----------------------------------------------
    hombro_izq = keypoints_validos['hombro_izq']
    hombro_der = keypoints_validos['hombro_der']
    nariz      = keypoints_validos['nariz']

    if not all(k is not None for k in [hombro_izq, hombro_der, nariz]):
        return "Normal"

    # ----------------------------------------------
    # 3.1. Detectar "Pelear"
    # ----------------------------------------------
    codo_izq   = keypoints_validos['codo_izq']
    codo_der   = keypoints_validos['codo_der']
    muneca_izq = keypoints_validos['muneca_izq']
    muneca_der = keypoints_validos['muneca_der']

    if all(k is not None for k in [codo_izq, codo_der, muneca_izq, muneca_der]):
        ang_codo_izq = calcular_angulo(hombro_izq, codo_izq, muneca_izq)
        ang_codo_der = calcular_angulo(hombro_der, codo_der, muneca_der)

        tolerancia_altura = 40
        muneca_izq_cerca = abs(muneca_izq[1] - hombro_izq[1]) <= tolerancia_altura
        muneca_der_cerca = abs(muneca_der[1] - hombro_der[1]) <= tolerancia_altura


        if (muneca_izq_cerca and muneca_der_cerca
            and ang_codo_izq < 90 and ang_codo_der < 90):
            return "Pelear"

    # ----------------------------------------------
    # 3.2. Detectar "Acostado"
    # ----------------------------------------------
    cadera_izq = keypoints_validos['cadera_izq']
    cadera_der = keypoints_validos['cadera_der']

    if all(k is not None for k in [cadera_izq, cadera_der]):
        x1, y1, x2, y2 = bounding_box_persona(keypoints)
        width = x2 - x1
        height = y2 - y1

        bbox_ratio = width / (height + 1e-6)
        avg_hombros_y = (hombro_izq[1] + hombro_der[1]) / 2.0
        avg_caderas_y = (cadera_izq[1] + cadera_der[1]) / 2.0
        diff_torso_y = abs(avg_hombros_y - avg_caderas_y)

        if (bbox_ratio > 2.0 and diff_torso_y < 40):
            return "Acostado"

    # ----------------------------------------------
    # 3.3. Detectar "Trepar"
    # ----------------------------------------------
    ojo_izq = keypoints_validos['ojo_izq']
    ojo_der = keypoints_validos['ojo_der']

    if all(k is not None for k in [codo_izq, codo_der, muneca_izq, muneca_der, ojo_izq, ojo_der]):
        margen_alto_codo = 30
        margen_alto_muneca = 20

        codos_arriba = (
            codo_izq[1] < (hombro_izq[1] - margen_alto_codo) and
            codo_der[1] < (hombro_der[1] - margen_alto_codo)
        )
        munecas_arriba = (
            muneca_izq[1] < (min(ojo_izq[1], ojo_der[1]) - margen_alto_muneca) and
            muneca_der[1] < (min(ojo_izq[1], ojo_der[1]) - margen_alto_muneca)
        )


        if codos_arriba and munecas_arriba:
            ang_codo_izq = calcular_angulo(hombro_izq, codo_izq, muneca_izq)
            ang_codo_der = calcular_angulo(hombro_der, codo_der, muneca_der)
            rango_min, rango_max = 30, 160
            codo_i_ok = (rango_min < ang_codo_izq < rango_max)
            codo_d_ok = (rango_min < ang_codo_der < rango_max)


            if codo_i_ok and codo_d_ok:
                return "Trepar"

    # ----------------------------------------------
    # 3.4. Si nada coincide, "Normal"
    # ----------------------------------------------
    return "Normal"

# ---------------------------------------------------
# 4. Función principal de procesar cada frame
# ---------------------------------------------------
def procesar_frame(frame):
    """
    1. Aplica el modelo YOLO para detectar keypoints de cada persona en el frame.
    2. Determina la actividad y dibuja la etiqueta correspondiente en la imagen.
    3. Retorna la imagen anotada y una lista de eventos (todos menos "Normal").
    """
    results = model.predict(frame, device=device, verbose=False)
    annotated_frame = results[0].plot()  # Anota el primer resultado

    eventos = []

    for result in results:
        if result.keypoints is not None:
            keypoints_all = result.keypoints.data.cpu().numpy()

            for person_keypoints in keypoints_all:
                # Ajustar forma si viene como (1, 17, 3)
                if person_keypoints.shape == (1, 17, 3):
                    person_keypoints = person_keypoints[0]

                if person_keypoints.shape == (17, 3):
                    actividad = detectar_actividad(person_keypoints)

                    # Puntos [5,6,11,12] => hombros y caderas para ubicar texto
                    puntos_clave_indices = [5, 6, 11, 12]
                    subset_points = person_keypoints[puntos_clave_indices, :2]
                    centro_x = int(np.mean(subset_points[:, 0]))
                    centro_y = int(np.mean(subset_points[:, 1]))

                    # Dibuja la actividad en la imagen
                    cv2.putText(
                        annotated_frame,
                        actividad,
                        (centro_x, centro_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 255),
                        2
                    )

                    # Cualquier actividad que no sea "Normal" se registra como evento
                    if actividad != "Normal":
                        eventos.append({"etiqueta": actividad, "confianza": 1.0})

    return annotated_frame, eventos
