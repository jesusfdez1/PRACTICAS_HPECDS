from flask import request
import os
import threading
from constants import PATH_PDFS
from data_chunking_embedding import procesar_documentos

def importar_archivos():
    archivos = request.files.getlist("files[]")
    lista_archivos_guardados = []

    # Si no existe la carpeta pdfs, se crea
    try:
        os.makedirs(PATH_PDFS, exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        return "", 500

    for archivo in archivos:
        try:
            path_archivo = f'{PATH_PDFS}/{archivo.filename}'
            archivo.save(path_archivo)
            lista_archivos_guardados.append(path_archivo)
        except Exception as e:
            print(f"Error al guardar archivo: {e}")
            return "", 500
    # Iniciar un hilo para procesar los archivos PDF en segundo plano
    hilo_procesar = threading.Thread(target=procesar_documentos, args=(lista_archivos_guardados,))
    hilo_procesar.start()

    # Devolver respuesta inmediata
    return "", 200
