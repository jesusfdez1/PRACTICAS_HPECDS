from datetime import datetime
from datetime import timedelta
from flask import Flask
from flask import request
import os
from constants import API_MICROSERVICES_BASE_URL, API_MICROSERVICES_PORT, PATH

app = Flask(__name__)
@app.route("/importer", methods=["POST"])
def import_data():
    print(PATH)
    files = request.files.getlist("files[]")
    #Si no existe la carpeta pdfs, se crea
    try:
        os.makedirs(f'{PATH}/pdfs', exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        
    for file in files:
        file.save(f'{PATH}/pdfs/{file.filename}')
    return "OK"



if __name__ == "__main__":
    from waitress import serve
    from flask_cors import CORS
    CORS(app)    
    serve(app, host=API_MICROSERVICES_BASE_URL, port=API_MICROSERVICES_PORT)