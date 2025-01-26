# run.py
from app import app
import callbacks  # Importa los callbacks para que se registren en la app

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=8050,debug=True)
