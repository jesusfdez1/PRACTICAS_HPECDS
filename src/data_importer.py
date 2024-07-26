from datetime import datetime
from datetime import timedelta
from flask import Flask
from flask import request
import os
from constants import API_MICROSERVICES_BASE_URL, API_MICROSERVICES_PORT, PATH_PDFS

app = Flask(__name__)
@app.route("/importer", methods=["POST"])
def import_data():
    files = request.files.getlist("files[]")
    # Si no existe la carpeta pdfs, se crea
    try:
        os.makedirs(PATH_PDFS, exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        return "Internal Server Error", 500
        
    for file in files:
        try:
            file.save(f'{PATH_PDFS}/{file.filename}')
        except:
            return "Internal Server Error", 500
    return "OK", 200

if __name__ == "__main__":
    from waitress import serve
    from flask_cors import CORS
    CORS(app)    
    serve(app, host=API_MICROSERVICES_BASE_URL, port=API_MICROSERVICES_PORT)