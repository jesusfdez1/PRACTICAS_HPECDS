from flask import request
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from constants import PATH_PDFS, NUM_HILOS
from data_chunking_embedding import procesar_documentos

def guardar_archivo(archivo):
    try:
        path_archivo = f'{PATH_PDFS}/{archivo.filename}'
        archivo.save(path_archivo)
        return path_archivo
    except Exception as e:
        print(f"Error al guardar archivo: {e}")
        return None

def importar_archivos():
    archivos = request.files.getlist("files[]")
    lista_archivos_guardados = []

    # Si no existe la carpeta pdfs, se crea
    try:
        os.makedirs(PATH_PDFS, exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        return "", 500

    # Usar ThreadPoolExecutor para guardar los archivos en paralelo
    with ThreadPoolExecutor(max_workers=NUM_HILOS) as executor:
        resultados = list(executor.map(guardar_archivo, archivos))

    # Filtrar los archivos que se guardaron correctamente
    lista_archivos_guardados = [path for path in resultados if path is not None]

    if not lista_archivos_guardados:
        print("No se pudieron guardar los archivos.")
        return "", 500

    # Iniciar un hilo para procesar los archivos PDF en segundo plano
    hilo_procesar = threading.Thread(target=procesar_documentos, args=(lista_archivos_guardados,))
    hilo_procesar.start()

    # Devolver respuesta inmediata
    return "", 200
