from langchain_community.embeddings.ollama import OllamaEmbeddings
from flask import request
from constants import CHUNK_SIZE, CHUNK_OVERLAP, PATH_PDFS
import fitz
import datetime
import re
import os

def get_embedding_function():
   # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    embeddings = OllamaEmbeddings(model="joanfm/jina-embeddings-v2-base-es")
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
    # Si no existe la carpeta pdfs, error
    if not os.path.exists(PATH_PDFS):
        return list(fechas)
    
    for archivo in os.listdir(PATH_PDFS):
        fecha = obtener_fecha_individual(archivo)
        if fecha is not None:
            fechas.add(fecha)
    fechas_formateadas = []
    for fecha in fechas:
        fecha_formateada = fecha.strftime("%d/%m/%Y")
        fechas_formateadas.append(fecha_formateada)
    return sorted(fechas_formateadas)

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
                    return ultima_fecha
                except ValueError:
                    # Si no se puede convertir, intentar con otro valor
                    ultimo_valor = palabras_clave.split(";")[3].strip()
                    return obtener_fecha_desde_texto(ultimo_valor)
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
