from flask import Flask
from waitress import serve
from flask_cors import CORS
from data_importer import import_data
from data_downloader import receptor_fechas
from constants import API_MICROSERVICES_BASE_URL, API_MICROSERVICES_PORT

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde cualquier origen

# Ruta para el importador de datos
app.route("/importer", methods=["POST"])(import_data)
app.route("/downloader", methods=["POST"])(receptor_fechas)

if __name__ == "__main__":
    # Ejecutar la aplicación con Waitress en la dirección y puerto especificados
    serve(app, host=API_MICROSERVICES_BASE_URL, port=API_MICROSERVICES_PORT)
