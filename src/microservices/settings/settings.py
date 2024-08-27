import os
from flask import request, Flask
from waitress import serve
from flask_cors import CORS

def set_chunk_values():
    """
    Establece las variables de entorno `CHUNK_SIZE` y `CHUNK_OVERLAP` basándose en los datos JSON recibidos en una solicitud.
    
    :return: Devuelve una cadena vacía y un código de estado HTTP. Si el bloque try tiene éxito, devolverá una cadena vacía y
             un código de estado 200 (indicando éxito). Si ocurre una excepción durante el bloque try, devolverá una cadena vacía y un
             código de estado 500 (indicando un error interno del servidor).
    """
    try:
        datos = request.get_json()
        os.environ["CHUNK_SIZE"] = str(datos["chunkLength"])
        os.environ["CHUNK_OVERLAP"] = str(datos["contextLength"])
    except Exception as e:
        return "", 500
    return "", 200


def get_chunk_values():
    """
    Obtiene los valores de tamaño de fragmento y longitud de contexto.
    
    :return: Devuelve un diccionario con los valores de tamaño de fragmento y longitud de contexto.
    """
    return {
        "chunkLength": int(os.getenv("CHUNK_SIZE")),
        "contextLength": os.getenv("CHUNK_OVERLAP"),
    }, 200

app = Flask(__name__)
CORS(app)

# Ruta para el importador de datos
app.route("/settings", methods=["POST"])(set_chunk_values)
app.route("/settings", methods=["GET"])(get_chunk_values)

if __name__ == "__main__":
    serve(app, host=os.getenv('SETTINGS'), port=int(os.getenv('SETTINGS_PORT')))