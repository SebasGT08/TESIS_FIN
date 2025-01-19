from flask import Flask
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    register_routes(app)
    print("Rutas registradas:", app.url_map)  # <--- debug
    return app
