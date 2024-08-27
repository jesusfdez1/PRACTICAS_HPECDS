from flask import request, jsonify, Flask
from datetime import datetime
import json
from threading import Lock
from langchain_community.llms.ollama import Ollama
from langchain_community.embeddings.ollama import OllamaEmbeddings
import os
from waitress import serve
from flask_cors import CORS


lock = Lock()
def get_funcion_embebido() -> OllamaEmbeddings:
    """
    Devuelve una instancia de `OllamaEmbeddings` con un modelo y una URL base específicos.
    
    :return embeddings: Una instancia de la clase OllamaEmbeddings inicializada con los parámetros de modelo y URL base especificados.
    """
    embeddings = OllamaEmbeddings(
        model="joanfm/jina-embeddings-v2-base-es", base_url="http://ollama:11434"
    )
    return embeddings

def generar_titulo():
    """
    Toma los datos JSON, extrae los mensajes, los envía a un modelo de Ollama y devuelve el 
    texto de respuesta o un mensaje de chat predeterminado con la fecha y hora actual si ocurre una excepción.
    
    :return json: Devuelve una respuesta JSON que contiene el texto de respuesta generado por el modelo 
                  de Ollama basado en los mensajes de entrada del prompt, o una respuesta predeterminada si ocurre una 
                  excepción durante el proceso. La respuesta incluye el texto generado o un mensaje con marca de tiempo 
                  si ocurre un error.
    """
    try:
        datos = request.data.decode("utf-8")
        datosJSON = json.loads(datos) # Convertir los datos de texto JSON a un diccionario de Python
        mensajes = datosJSON.get("prompt", [])  # Obtener la lista de mensajes del diccionario
        modelo = Ollama(model=os.getenv("MODEL_LLM"), base_url="http://ollama:11434") # Enviar prompt a Ollama
        respuesta = modelo.invoke(mensajes)
        return jsonify({"response": respuesta})
    except Exception as e:
        return jsonify(
            {"response": "Chat del " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        )
        
app = Flask(__name__)
CORS(app)

# Ruta para el importador de datos
app.route("/generate", methods=["POST"])(generar_titulo)
if __name__ == "__main__":
    serve(app, host=os.getenv('GENERATE'), port=int(os.getenv('GENERATE_PORT')))