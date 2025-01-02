import threading
from .camera_handler import capturar_frames
from . import create_app
from .app_fastapi import app as fastapi_app  # Aquí el cambio
import uvicorn

# Flask App
flask_app = create_app()

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def run_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Iniciar el hilo para capturar frames
    threading.Thread(target=capturar_frames, daemon=True).start()

    # Ejecutar Flask y FastAPI en hilos separados
    threading.Thread(target=run_flask, daemon=True).start()
    run_fastapi()  # Bloqueante: FastAPI se ejecuta en el hilo principal
