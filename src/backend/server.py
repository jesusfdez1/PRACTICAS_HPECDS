from flask import Flask
import os
from waitress import serve
from flask_cors import CORS
from importer import importar_archivos
from downloader import receptor_fechas
from chunking import limpiar_chroma
from query import procesar_peticion, generar_titulo
from embeddings import set_chunk_values, get_chunk_values, get_fechas_archivos

app = Flask(__name__)
CORS(app)  # Habilitar CORS para permitir peticiones desde cualquier origen

# Ruta para el importador de datos
app.route("/importer", methods=["POST"])(importar_archivos)
app.route("/downloader", methods=["POST"])(receptor_fechas)
app.route("/chat", methods=["POST"])(procesar_peticion)
app.route("/settings", methods=["POST"])(set_chunk_values)
app.route("/settings", methods=["GET"])(get_chunk_values)
app.route("/dates", methods=["GET"])(get_fechas_archivos)
app.route("/generate", methods=["POST"])(generar_titulo)
app.route("/clean", methods=["DELETE"])(limpiar_chroma)

if __name__ == "__main__":
    PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ['PATH_LOG'] = f'{PATH}/log.txt'
    os.environ['PATH_PDFS'] = f'{PATH}/data'
    os.environ['PATH_JSON'] = f"{os.getenv('PATH_PDFS')}/dates.json"
    os.environ['CHROMA_PATH'] = f"{os.getenv('PATH_PDFS')}/chroma"
    os.environ['API_MICROSERVICES_BASE_URL'] = '0.0.0.0'
    os.environ['API_MICROSERVICES_PORT'] = '3001'
    os.environ['CHUNK_SIZE'] = '500'
    os.environ['CHUNK_OVERLAP'] = '90'
    os.environ['MAX_TOKENS'] = '4096'
    os.environ['NUM_HILOS'] = '8'
    os.environ['MODEL_LLM'] = 'llama3.1:8b-instruct-q5_K_M'
    
     # Ejecutar la aplicación con Waitress en la dirección y puerto especificados
    serve(app, host=os.getenv('API_MICROSERVICES_BASE_URL'), port=os.getenv('API_MICROSERVICES_PORT'))

