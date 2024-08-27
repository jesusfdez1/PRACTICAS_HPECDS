import os
import json
from flask import Flask
from waitress import serve
from flask_cors import CORS

def get_fechas_archivos():
    """
    Lee las fechas de un archivo JSON, almacena las fechas únicas en un conjunto y las devuelve ordenadas.
    
    :return fechas: Devuelve una lista ordenada de fechas únicas extraídas de un archivo JSON.
    """
    fechas = set()
    # Verificar si el archivo JSON existe
    if os.path.exists(os.getenv("PATH_JSON")):
        with open(os.getenv("PATH_JSON"), "r") as archivo_json:
            datos = json.load(archivo_json)
        # Agregar todas las fechas únicas al conjunto
        for fecha in datos.values():
            fechas.add(fecha)
    # Retornar la lista de fechas únicas, ordenada
    return sorted(fechas)

app = Flask(__name__)
CORS(app)

# Ruta para el importador de datos
app.route("/dates", methods=["GET"])(get_fechas_archivos)

if __name__ == "__main__":
    serve(app, host=os.getenv('DATES'), port=int(os.getenv('DATES_PORT')))