from ultralytics import YOLO
import torch
import os

# Construye la ruta absoluta al modelo
base_dir = os.path.dirname(__file__)  # Directorio del archivo actual
model_path = os.path.abspath(os.path.join(base_dir, "../models/object-detection_s.pt"))
model = YOLO(model_path)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)
model.conf = 0.25  # Ajusta el umbral de confianza

def procesar_objetos(frame, prev_time):
    """
    Procesa un frame para detectar objetos y los anota.
    """
    results = model.predict(frame, device=device, verbose=False)
    annotated_frame = results[0].plot()  # Renderiza las detecciones en el frame
    
    eventos = []

    for detection in results[0].boxes:
        clase = detection.cls
        confianza = detection.conf
        etiqueta = model.names[int(clase)]
        if etiqueta in ["pistol", "knife"]:  # Clases relevantes
            eventos.append({"etiqueta": etiqueta, "confianza": confianza.item()})

    return annotated_frame, eventos, prev_time
