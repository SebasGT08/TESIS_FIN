from flask import Flask
from .routes import register_routes
from .sockets import register_socket_events, socketio

def create_app():
    app = Flask(__name__)
    register_routes(app)
    register_socket_events(app)
    
    return app
