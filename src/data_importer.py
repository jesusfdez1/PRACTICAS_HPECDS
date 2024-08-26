from flask import request
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from data_chunking_embedding import procesar_documentos


def guardar_archivo(archivo):
    """
    Guarda un archivo subido en una ruta especificada y devuelve la ruta del archivo.
    
    :param archivo: Representa el objeto de archivo que se está subiendo. La función intenta guardar el 
                    archivo en una ruta especificada y devuelve la ruta donde se guarda el archivo si tiene éxito. Si 
                    ocurre un error durante el proceso, se devuelve `None`.
    :return ruta_archivo: Devuelve la ruta del archivo guardado si se guarda correctamente, o `None` si hay un error 
             durante el proceso.
    """
    try:
        ruta_archivo = f"{os.getenv('PATH_PDFS')}/{archivo.filename}"
        archivo.save(ruta_archivo)
        return ruta_archivo
    except Exception as e:
        print(f"Error al guardar archivo: {e}")
        return None

def importar_archivos():
    """
    Importa archivos, los guarda en paralelo utilizando ThreadPoolExecutor, filtra los archivos 
    guardados correctamente y comienza un hilo para procesar los archivos PDF en segundo plano.
    
    :return: Devuelve una cadena vacía `""` y el código de estado `200` si los archivos se procesaron 
             y guardaron correctamente. Si hubo un problema al guardar los archivos o no se guardaron archivos, 
             devuelve una cadena vacía `""` y el código de estado `500`.
    """
    archivos = request.files.getlist("files[]")
    lista_archivos_guardados = []

    # Si no existe la carpeta pdfs, se crea
    try:
        os.makedirs(os.getenv("PATH_PDFS"), exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        return "", 500

    # Usar ThreadPoolExecutor para guardar los archivos en paralelo
    with ThreadPoolExecutor(max_workers=int(os.getenv("NUM_HILOS"))) as executor:
        resultados = list(executor.map(guardar_archivo, archivos))

    # Filtrar los archivos que se guardaron correctamente
    lista_archivos_guardados = [path for path in resultados if path is not None]

    if not lista_archivos_guardados:
        print("No se pudieron guardar los archivos.")
        return "", 500

    # Iniciar un hilo para procesar los archivos PDF en segundo plano
    hilo_procesar = threading.Thread(
        target=procesar_documentos, args=(lista_archivos_guardados,)
    )
    hilo_procesar.start()

    # Devolver respuesta inmediata
    return "", 200
