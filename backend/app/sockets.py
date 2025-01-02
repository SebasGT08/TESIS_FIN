# sockets.py
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")


def register_socket_events(app):
    socketio.init_app(app)

    @socketio.on('connect')
    def on_connect():
        print("[DEBUG] Cliente conectado.")
        

    @socketio.on('disconnect')
    def on_disconnect():
        print("[DEBUG] Cliente desconectado.")
