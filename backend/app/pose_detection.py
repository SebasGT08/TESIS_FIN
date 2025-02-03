import os
import cv2
import torch
import numpy as np
from ultralytics import YOLO

# ---------------------------------------------------
# 1. Configuración del modelo YOLO
# ---------------------------------------------------
base_dir = os.path.dirname(__file__)  # Directorio del archivo actual
model_path = os.path.abspath(os.path.join(base_dir, "../models/yolo11s-pose.pt"))

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
    if np.linalg.norm(ba) == 0 or np.linalg.norm(bc) == 0:
        return 180  # Si el vector es nulo, devolvemos un ángulo alto por defecto
    cos_angle = np.dot(ba, bc) / ((np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))

def distancia(a, b):
    """
    Calcula la distancia euclidiana entre dos puntos 2D (x1, y1) y (x2, y2).
    """
    return np.linalg.norm(a[:2] - b[:2])

def obtener_keypoints_validos(keypoints, indices, threshold=0.5):
    """
    Filtra y devuelve los keypoints válidos según el índice y un umbral de confianza.
    """
    keypoints_validos = {}
    for nombre, idx in indices.items():
        kp = keypoints[idx] if idx < len(keypoints) else None
        keypoints_validos[nombre] = (
            kp if kp is not None and kp[2] >= threshold else None
        )
    return keypoints_validos

# ---------------------------------------------------
# 3. Lógica de detección de actividad
# ---------------------------------------------------

def calcular_confianza_pelear(keypoints_validos, tolerancia_altura=60):
    """
    Calcula un valor de confianza para la actividad "Pelear".
    """
    hombro_izq = keypoints_validos['hombro_izq']
    hombro_der = keypoints_validos['hombro_der']
    codo_izq = keypoints_validos['codo_izq']
    codo_der = keypoints_validos['codo_der']
    muneca_izq = keypoints_validos['muneca_izq']
    muneca_der = keypoints_validos['muneca_der']

    # Verificar si las munecas están a la altura de los hombros
    muneca_izq_cerca = abs(muneca_izq[1] - hombro_izq[1]) <= tolerancia_altura
    muneca_der_cerca = abs(muneca_der[1] - hombro_der[1]) <= tolerancia_altura

    # Calcular la distancia normalizada entre las munecas y compararla con la distancia entre los hombros
    distancia_hombros = distancia(hombro_izq, hombro_der)
    distancia_munecas = distancia(muneca_izq, muneca_der)
    separacion_ok = distancia_munecas <= distancia_hombros

    # Verificar que las munecas están por encima de los codos
    muneca_sobre_codo_izq = (muneca_izq[1] <= codo_izq[1] )
    muneca_sobre_codo_der = (muneca_der[1] <= codo_der[1])

    # Calcular confianza final
    confianza = 0
    if muneca_izq_cerca:
        confianza += 0.225
    if muneca_der_cerca:
        confianza += 0.225
    if separacion_ok:
        confianza += 0.15
    if muneca_sobre_codo_izq:
        confianza += 0.2
    if muneca_sobre_codo_der:
        confianza += 0.2
    
    # print('Pelear:', confianza)
    
    return confianza

def calcular_confianza_trepar(keypoints_validos, distancia_min_piernas=20):
    """
    Calcula un valor de confianza para la actividad "Trepar".
    """
    hombro_izq = keypoints_validos['hombro_izq']
    hombro_der = keypoints_validos['hombro_der']
    muneca_izq = keypoints_validos['muneca_izq']
    muneca_der = keypoints_validos['muneca_der']
    nariz = keypoints_validos.get('nariz', None)
    ojo_izq = keypoints_validos.get('ojo_izq', None)
    ojo_der = keypoints_validos.get('ojo_der', None)
    oreja_izq = keypoints_validos.get('oreja_izq', None)
    oreja_der = keypoints_validos.get('oreja_der', None)
    rodilla_izq = keypoints_validos.get('rodilla_izq', None)
    rodilla_der = keypoints_validos.get('rodilla_der', None)

    # Verificar altura de referencia (nariz, ojos, orejas)
    referencias = [
        nariz, ojo_izq, ojo_der, oreja_izq, oreja_der
    ]
    referencias_validas = [ref[1] for ref in referencias if ref is not None]

    if not referencias_validas:
        return 0  # No hay referencias para calcular

    referencia_altura = min(referencias_validas)

    # Asignar puntaje proporcional solo si las muñecas están por encima de la referencia
    def calcular_puntaje_muneca(muneca, referencia):
        if muneca[1] < referencia:
            return min(3.5, 3.5 * (referencia - muneca[1]) / referencia)  # Puntaje proporcional
        return 0

    puntaje_muneca_izq = calcular_puntaje_muneca(muneca_izq, referencia_altura)
    puntaje_muneca_der = calcular_puntaje_muneca(muneca_der, referencia_altura)

    # Verificar levantamiento de piernas
    pierna_levantada = 0
    if rodilla_izq is not None and rodilla_der is not None:
        if abs(rodilla_izq[1] - rodilla_der[1]) > distancia_min_piernas:
            pierna_levantada = 3

    # Calcular confianza final
    confianza = puntaje_muneca_izq + puntaje_muneca_der + pierna_levantada

    # print('Trepar:', confianza)
    return min(confianza, 1)  # Limitar la confianza máxima a 1

def calcular_confianza_acostado(keypoints_validos):
    """
    Calcula un valor de confianza para la actividad "Acostado".
    """
    hombro_izq = keypoints_validos['hombro_izq']
    hombro_der = keypoints_validos['hombro_der']
    cadera_izq = keypoints_validos['cadera_izq']
    cadera_der = keypoints_validos['cadera_der']

    # Calcular bounding box basado en keypoints
    x_coords = [kp[0] for kp in [hombro_izq, hombro_der, cadera_izq, cadera_der] if kp is not None]
    y_coords = [kp[1] for kp in [hombro_izq, hombro_der, cadera_izq, cadera_der] if kp is not None]

    if len(x_coords) < 4 or len(y_coords) < 4:
        return 0  # No hay suficientes keypoints para calcular

    width = max(x_coords) - min(x_coords)
    height = max(y_coords) - min(y_coords)

    # Proporción del bounding box
    bbox_ratio = width / (height + 1e-6)

    # Diferencia en altura entre hombros y caderas
    avg_hombros_y = (hombro_izq[1] + hombro_der[1]) / 2.0
    avg_caderas_y = (cadera_izq[1] + cadera_der[1]) / 2.0
    diff_torso_y = abs(avg_hombros_y - avg_caderas_y)

    # Determinar confianza basada en alineación y proporción
    confianza = 0
    if bbox_ratio > 2.0:  # Bounding box ancho
        confianza += 0.7
    if diff_torso_y < 20:  # Alineación horizontal
        confianza += 0.3

    # print('Acostado:', confianza)
    return min(confianza, 1)

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
        return "Normal", 0

    # Diccionario para obtener los keypoints necesarios
    indices = {
        'hombro_izq': 5, 'hombro_der': 6,
        'codo_izq': 7, 'codo_der': 8,
        'muneca_izq': 9, 'muneca_der': 10,
        'nariz': 0, 'ojo_izq': 1, 'ojo_der': 2,
        'oreja_izq': 3, 'oreja_der': 4,
        'rodilla_izq': 13, 'rodilla_der': 14,
        'cadera_izq': 11, 'cadera_der': 12
    }

    keypoints_validos = obtener_keypoints_validos(keypoints, indices, CONFIDENCE_THRESHOLD)

    # Verificar que existan al menos los keypoints necesarios para "Pelear"
    necesarios_pelear = ['hombro_izq', 'hombro_der', 'codo_izq', 'codo_der', 'muneca_izq', 'muneca_der']
    if all(keypoints_validos[nombre] is not None for nombre in necesarios_pelear):
        confianza_pelear = calcular_confianza_pelear(keypoints_validos)
        if confianza_pelear >= 0.7:  # Umbral para considerar que está "Peleando"
            return "Pelear", confianza_pelear
    
    # Verificar que existan al menos los keypoints necesarios para "Trepar"
    necesarios_trepar = ['hombro_izq', 'hombro_der', 'muneca_izq', 'muneca_der']
    if all(keypoints_validos[nombre] is not None for nombre in necesarios_trepar):
        confianza_trepar = calcular_confianza_trepar(keypoints_validos)
        if confianza_trepar >= 0.7:  # Umbral para considerar que está "Trepando"
            return "Trepar", confianza_trepar

    # Verificar que existan al menos los keypoints necesarios para "Acostado"
    necesarios_acostado = ['hombro_izq', 'hombro_der', 'cadera_izq', 'cadera_der']
    if all(keypoints_validos[nombre] is not None for nombre in necesarios_acostado):
        confianza_acostado = calcular_confianza_acostado(keypoints_validos)
        if confianza_acostado >= 0.7:  # Umbral para considerar que está "Acostado"
            return "Acostado", confianza_acostado
    
    return "Normal", 0

# ---------------------------------------------------
# 4. Función principal de procesar cada frame
# ---------------------------------------------------
def procesar_frame(frame, prev_time, track_id_to_name):
    """
    1. Aplica el modelo YOLO para detectar keypoints de cada persona en el frame.
    2. Determina la actividad y dibuja la etiqueta correspondiente en la imagen.
    3. Dibuja keypoints y líneas conectándolos para cada persona detectada.
    4. Retorna la imagen anotada y una lista de eventos (todos menos "Normal").
    """
    # Realizar la predicción con el modelo YOLO
    results = model.predict(frame, device=device, verbose=False)

    # Crear una copia del frame para anotarlo
    annotated_frame = frame.copy()

    # Lista para almacenar los eventos detectados
    eventos = []

    # Colores para keypoints y líneas
    keypoint_color = (0, 255, 0)  # Verde
    line_color = (255, 0, 0)  # Azul

    for result in results:
        if result.keypoints is not None:
            # Obtener los keypoints detectados y convertirlos a numpy
            keypoints_all = result.keypoints.data.cpu().numpy()

            for person_keypoints in keypoints_all:
                # Ajustar forma si viene como (1, 17, 3)
                if person_keypoints.shape == (1, 17, 3):
                    person_keypoints = person_keypoints[0]

                if person_keypoints.shape == (17, 3):
                    # Dibuja los keypoints como círculos en la imagen
                    for kp in person_keypoints:
                        x, y, conf = kp
                        if conf > 0.5:  # Solo dibujar keypoints confiables
                            cv2.circle(annotated_frame, (int(x), int(y)), 5, keypoint_color, -1)

                    # Conexiones entre keypoints para formar un esqueleto
                    skeleton_connections = [
                        (5, 6), (5, 11), (6, 12), (11, 12),  # Hombros y caderas
                        (5, 7), (7, 9), (6, 8), (8, 10),      # Brazos
                        (11, 13), (13, 15), (12, 14), (14, 16) # Piernas
                    ]

                    for start, end in skeleton_connections:
                        if person_keypoints[start][2] > 0.5 and person_keypoints[end][2] > 0.5:
                            x1, y1 = person_keypoints[start][:2]
                            x2, y2 = person_keypoints[end][:2]
                            cv2.line(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), line_color, 2)

                    # Determinar la actividad basada en los keypoints
                    actividad, confianza = detectar_actividad(person_keypoints)

                    # Calcular el centro de los hombros y caderas para posicionar el texto
                    puntos_clave_indices = [5, 6, 11, 12]
                    subset_points = person_keypoints[puntos_clave_indices, :2]
                    centro_x = int(np.mean(subset_points[:, 0]))
                    centro_y = int(np.mean(subset_points[:, 1]))

                    # Dibujar la actividad detectada en la imagen
                    cv2.putText(
                        annotated_frame,
                        actividad + f" ({confianza:.2f})",
                        (centro_x, centro_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 255),
                        2
                    )

                    # Registrar el evento si la actividad no es "Normal"
                    if actividad != "Normal":
                        eventos.append({"etiqueta": actividad, "confianza": confianza})

    return annotated_frame, eventos, prev_time

