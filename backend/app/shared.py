# shared.py
import multiprocessing

_reload_encodings_flag = None

def get_reload_flag():
    global _reload_encodings_flag
    if _reload_encodings_flag is None:
        # Se crea el manager y el flag sólo una vez
        manager = multiprocessing.Manager()
        _reload_encodings_flag = manager.Value('b', False)
    return _reload_encodings_flag
