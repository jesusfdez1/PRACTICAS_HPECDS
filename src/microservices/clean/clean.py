import os
from flask import Flask
from waitress import serve
from flask_cors import CORS
from langchain_chroma import Chroma

def limpiar_chroma():
    """
    Intenta eliminar una colección de Chroma y un archivo JSON si existen, devolviendo un código de estado de éxito o error.
    
    :return: Una cadena vacía y un código de estado de 200 si la función se ejecuta correctamente. Si ocurre una excepción,
             se devuelve una cadena vacía y un código de estado de 500.
    """
    try:
        if os.path.exists(os.getenv("CHROMA_PATH")):
            db = Chroma(persist_directory=os.getenv("CHROMA_PATH"))
            db.delete_collection()
        # Si existe el archivo os.getenv('PATH_JSON'))
        if os.path.isfile(os.getenv("PATH_JSON")):
            os.remove(os.getenv("PATH_JSON"))
        return "", 200
    except Exception as e:
        return "", 500
    
    
app = Flask(__name__)
CORS(app)

# Ruta para el importador de datos
app.route("/clean", methods=["DELETE"])(limpiar_chroma)

if __name__ == "__main__":
    serve(app, host=os.getenv('CLEAN'), port=int(os.getenv('CLEAN_PORT')))