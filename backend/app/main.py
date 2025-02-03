# main.py
import multiprocessing
from .shared import get_reload_flag

def run_flask(shared_flag):
    from . import create_app
    flask_app = create_app()
    # Inyecta el flag compartido en la configuración
    flask_app.config['reload_encodings_flag'] = shared_flag
    flask_app.run(host="0.0.0.0", port=5000)

def run_fastapi(pose_queue, object_queue, face_queue, event_queue):
    from .app_fastapi import set_queues
    from .app_fastapi import app as fastapi_app
    import uvicorn
    set_queues(pose_queue, object_queue, face_queue, event_queue)
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

def run_camera_handler(pose_queue, object_queue, face_queue, event_queue, detection_history, track_id_to_name, reload_encodings_flag):
    from .camera_handler import set_queues, capturar_frames
    # Se pasa el flag compartido a la función set_queues para que esté disponible en el módulo de detección
    set_queues(pose_queue, object_queue, face_queue, event_queue, detection_history, track_id_to_name, reload_encodings_flag)
    capturar_frames()

if __name__ == "__main__":
    multiprocessing.freeze_support()

    manager = multiprocessing.Manager()
    pose_queue    = manager.Queue(maxsize=10)
    object_queue  = manager.Queue(maxsize=10)
    face_queue    = manager.Queue(maxsize=10)
    event_queue   = manager.Queue(maxsize=50)

    detection_history = manager.dict()
    track_id_to_name  = manager.dict()

    # Aquí se crea el flag compartido: un valor booleano inicializado en False
    reload_encodings_flag = get_reload_flag()

    flask_process = multiprocessing.Process(target=run_flask, args=(reload_encodings_flag,))
    fastapi_process = multiprocessing.Process(
        target=run_fastapi, args=(pose_queue, object_queue, face_queue, event_queue)
    )
    detection_process = multiprocessing.Process(
        target=run_camera_handler,
        args=(pose_queue, object_queue, face_queue, event_queue, detection_history, track_id_to_name, reload_encodings_flag)
    )

    flask_process.start()
    fastapi_process.start()
    detection_process.start()

    flask_process.join()
    fastapi_process.join()
    detection_process.join()
