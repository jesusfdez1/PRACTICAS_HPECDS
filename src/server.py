from flask import Flask
from waitress import serve
from flask_cors import CORS
from data_importer import import_data, data_dates
from data_downloader import receptor_fechas
from data_query import procesar_peticion
from constants import API_MICROSERVICES_BASE_URL, API_MICROSERVICES_PORT
from embedding_function import set_chunk_values, get_chunk_values

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde cualquier origen

# Ruta para el importador de datos
app.route("/importer", methods=["POST"])(import_data)
app.route("/downloader", methods=["POST"])(receptor_fechas)
app.route("/chat", methods=["POST"])(procesar_peticion)
app.route("/settings", methods=["POST"])(set_chunk_values)
app.route("/settings", methods=["GET"])(get_chunk_values)
app.route("/dates", methods=["GET"])(data_dates)

if __name__ == "__main__":
    # Ejecutar la aplicación con Waitress en la dirección y puerto especificados
    serve(app, host=API_MICROSERVICES_BASE_URL, port=API_MICROSERVICES_PORT)
