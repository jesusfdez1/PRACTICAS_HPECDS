from flask import request
import os
from constants import PATH_PDFS

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
        except Exception as e:
            print(f"Error al guardar archivo: {e}")
            return "Internal Server Error", 500

    return "OK", 200
