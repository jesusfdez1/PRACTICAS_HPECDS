from langchain_community.embeddings.ollama import OllamaEmbeddings
from flask import request
from constants import CHUNK_SIZE, CHUNK_OVERLAP, PATH_PDFS, PATH_JSON
import fitz
import datetime
import re
import os
import json
import threading

nombre_archivo_json = "dates.json"


# Crear un lock global
json_lock = threading.Lock()

def guardar_fecha_en_json(archivo, fecha):
    # Leer datos existentes del archivo JSON
    with json_lock:
        if os.path.exists(PATH_JSON):
            with open(PATH_JSON, "r") as archivo_json:
                datos = json.load(archivo_json)
        else:
            datos = {}

        nombre_base_archivo = os.path.basename(archivo)
        fecha_formateada = fecha.strftime("%d/%m/%Y")
        # Actualizar o agregar la fecha en el diccionario
        datos[nombre_base_archivo] = fecha_formateada

        # Guardar el diccionario actualizado en el archivo JSON
        with open(PATH_JSON, "w") as archivo_json:
            json.dump(datos, archivo_json, indent=4)
        print(f"Fecha del archivo '{nombre_base_archivo}' guardada/actualizada en {nombre_archivo_json}")

def get_embedding_function():
   # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    embeddings = OllamaEmbeddings(model="joanfm/jina-embeddings-v2-base-es", base_url="http://ollama:11434")
    return embeddings

def set_chunk_values():
    global CHUNK_SIZE
    global CHUNK_OVERLAP
    try:
        data = request.get_json()
        CHUNK_SIZE = data["chunkLength"]
        CHUNK_OVERLAP = data["contextLength"]
    except Exception as e:
        return "", 500
    return "", 200

def get_chunk_values():
    return {"chunkLength": CHUNK_SIZE, "contextLength": CHUNK_OVERLAP}, 200

def obtener_fechas_archivos():
    fechas = set()

    # Verificar si el archivo JSON existe
    if os.path.exists(PATH_JSON):
        with open(PATH_JSON, "r") as archivo_json:
            datos = json.load(archivo_json)
        
        # Agregar todas las fechas únicas al conjunto
        for fecha in datos.values():
            fechas.add(fecha)
    
    # Retornar la lista de fechas únicas, ordenada
    return sorted(fechas)

def obtener_fecha_individual(archivo):
    ruta_archivo = os.path.join(PATH_PDFS, archivo)
    if os.path.isfile(ruta_archivo) and archivo.lower().endswith('.pdf'):
        try:
            # Abrir el archivo PDF y leer sus metadatos
            documento_pdf = fitz.open(ruta_archivo)
            metadatos = documento_pdf.metadata
            documento_pdf.close()
            
            # Obtener el campo "Palabras clave"
            palabras_clave = metadatos.get("keywords", "")
            # Obtener el último valor separado por ;
            if palabras_clave:
                ultimo_valor = palabras_clave.split(";")[-1].strip()
                try:
                    # Intentar convertir el último valor en una fecha
                    ultima_fecha = datetime.datetime.strptime(ultimo_valor, "%d/%m/%Y")
                    # Guardar la fecha en el archivo JSON
                    guardar_fecha_en_json(archivo, ultima_fecha)
                    return ultima_fecha
                except ValueError:
                    # Si no se puede convertir, intentar con otro valor
                    ultimo_valor = palabras_clave.split(";")[3].strip()
                    fecha_alternativa = obtener_fecha_desde_texto(ultimo_valor)
                    if fecha_alternativa:
                        # Guardar la fecha en el archivo JSON
                        guardar_fecha_en_json(archivo, fecha_alternativa)
                    return fecha_alternativa
        except Exception as e:
            print(f"Error al procesar archivo {archivo}: {e}")
            pass

def obtener_fecha_desde_texto(texto):
    patron_fecha = r'(?P<dia_semana>\w+)\s+(?P<dia>\d{1,2})\s+de\s+(?P<mes>\w+)\s+de\s+(?P<anio>\d{4})\s*'
    coincidencia_fecha = re.search(patron_fecha, texto, re.IGNORECASE)
    
    if coincidencia_fecha:
        dia = int(coincidencia_fecha.group('dia'))
        mes_str = coincidencia_fecha.group('mes').lower()
        anio = int(coincidencia_fecha.group('anio'))
        
        meses = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
        mes = meses.get(mes_str)
        
        if mes:
            return datetime.datetime(anio, mes, dia)
