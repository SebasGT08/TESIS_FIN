import multiprocessing
from .camera_handler import capturar_frames
from . import create_app
from .app_fastapi import app as fastapi_app
import uvicorn

# Flask App
flask_app = create_app()

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def run_fastapi(pose_queue, object_queue, face_queue, event_queue):
    # Asigna las colas compartidas al módulo de FastAPI
    from .app_fastapi import set_queues
    set_queues(pose_queue, object_queue, face_queue, event_queue)
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

def run_camera_handler(pose_queue, object_queue, face_queue, event_queue):
    # Asigna las colas compartidas al módulo de Camera Handler
    from .camera_handler import set_queues
    set_queues(pose_queue, object_queue, face_queue, event_queue)
    capturar_frames()

if __name__ == "__main__":
    # Usa freeze_support para compatibilidad con Windows
    multiprocessing.freeze_support()

    # Inicializa las colas compartidas
    manager = multiprocessing.Manager()
    pose_queue = manager.Queue(maxsize=10)
    object_queue = manager.Queue(maxsize=10)
    face_queue = manager.Queue(maxsize=10)
    event_queue = manager.Queue(maxsize=50)

    # Iniciar procesos
    flask_process = multiprocessing.Process(target=run_flask)
    fastapi_process = multiprocessing.Process(
        target=run_fastapi, args=(pose_queue, object_queue, face_queue, event_queue)
    )
    detection_process = multiprocessing.Process(
        target=run_camera_handler, args=(pose_queue, object_queue, face_queue, event_queue)
    )

    flask_process.start()
    fastapi_process.start()
    detection_process.start()

    # Mantener todos los procesos en ejecución
    flask_process.join()
    fastapi_process.join()
    detection_process.join()
