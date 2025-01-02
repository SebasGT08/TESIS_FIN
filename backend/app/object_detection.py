from ultralytics import YOLO
import cv2
import torch
import os

# Construye la ruta absoluta al modelo
base_dir = os.path.dirname(__file__)  # Directorio del archivo actual
model_path = os.path.abspath(os.path.join(base_dir, "../models/object-detection_v1.pt"))
model = YOLO(model_path)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
model.conf = 0.25  # Ajusta el umbral de confianza

def procesar_objetos(frame):
    """
    Procesa un frame para detectar objetos y los anota.
    """
    results = model.predict(frame, device=device, verbose=False)
    annotated_frame = results[0].plot()  # Renderiza las detecciones en el frame
    return annotated_frame
