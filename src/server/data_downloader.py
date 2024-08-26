import sys
import time
import threading
import requests
import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime
from datetime import timedelta
from flask import request
from data_chunking_embedding import procesar_documentos


global lista_archivos_guardados
lista_archivos_guardados = []


def escribir_log(mensaje):
    """
    Escribe un mensaje dado en un archivo de registro especificado por la variable de entorno `PATH_LOG`.
    
    :param mensaje: Representa el mensaje o información que se desea escribir en un archivo de registro
    """
    with open(os.getenv("PATH_LOG"), "a") as f:
        f.write(f"{mensaje}\n")
    f.close()


def controlador_error(response, url):
    """
    Maneja diferentes errores de código de estado HTTP mediante el registro, la visualización
    de mensajes y la toma de acciones específicas basadas en el código de error.
    
    :param response: El objeto de respuesta devuelto de una solicitud HTTP realizada utilizando una biblioteca 
                     como requests en Python. Contiene información como el código de estado y el contenido de la respuesta.
    :param url: URL a la que se intentaba acceder cuando ocurrió el error. Se utiliza en el mensaje de registro 
                para indicar qué URL causó el error.
    :return error: Devuelve el código de error si es 401, 404 o uno de los códigos de error del servidor (500, 501, 502, 503). Si el error es 
             403 (acceso no autorizado), el programa se cierra con un mensaje de error. Si no se cumplen ninguna de estas condiciones, 
             el programa se cierra con un mensaje de error inesperado.
    """
    error = response.status_code
    root = ET.fromstring(response.content)
    error_message = root.find(".//text").text
    escribir_log(f"{datetime.now()} - Error {error}: '{error_message}' al acceder a la {url}.")

    if error in [401, 404]:
        print(f"Error {error}: {error_message}")
        return error
    elif error == 403:
        sys.exit(f"Error {error}: Acceso no autorizado. Saliendo del programa...")
    elif error in [500, 501, 502, 503]:
        wait_time = 300  # 5 minutos
        print(f"Error {error}: Problema del servidor. Esperando {wait_time / 60} minutos antes de reintentar...")
        time.sleep(wait_time)
        return error
    else:
        sys.exit(f"Error inesperado: {error}: {error_message}. Saliendo del programa...")


def hacer_request_con_reintento(url, max_intentos=5, delay=350):
    """
    Realiza una solicitud a una URL con intentos de reintento y manejo de errores.
    
    :param url: URL del recurso al que desea hacer una solicitud. Es la dirección web a la que se enviará la 
                solicitud para recuperar datos o interactuar con un servicio web.
    :param max_intentos: Indica el número máximo de intentos que se realizarán al hacer una solicitud HTTP a la 
                         URL especificada en caso de que falle la primera vez. Especifica cuántas veces se, por defecto es 5 (opcional).
    :param delay: Representa el tiempo de espera en milisegundos entre los intentos de reintento cuando una solicitud falla. En esta función, 
                  después de encontrar un error durante la solicitud, el programa esperará el tiempo `delay` especificado antes de intentar 
                  la solicitud nuevamente, por defecto es 350 (opcional).
    :return respuesta: Devuelve el objeto `respuesta` si la solicitud es exitosa y el código de estado no es un error, un código de error
                      (401 o 404) si la respuesta indica un error, o `None` si todos los intentos de reintento fallan.
    """
    intentos = 0
    respuesta = None  # Inicializar response con None para evitar errores de que no está definido
    if intentos == max_intentos:
        sys.exit(f"Se alcanzó el número máximo de {max_intentos} intentos. Saliendo del programa...")
    while intentos < max_intentos:
        try:
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            }
            respuesta = requests.get(url, headers=headers)
            respuesta.raise_for_status()  # Lanzar una excepción para códigos de estado de error
            return respuesta
        except requests.exceptions.RequestException as e:
            if respuesta is not None:
                error = controlador_error(respuesta, url)
                if error in [401, 404]:
                    return error
            intentos += 1
            print(f"Reintento {intentos} de {max_intentos} tras error: {e}")
            time.sleep(delay)
    return None


def procesar_enlaces(enlaces):
    """
    Descarga archivos de una lista de enlaces, los guarda en un directorio especificado y registra cualquier error encontrado durante el proceso.
    
    :param enlaces: Lista de URL que se están procesando para descargar archivos. Cada URL en la lista se procesa para descargar el
    contenido del archivo correspondiente.
    """
    try:
        os.makedirs(os.getenv("PATH_PDFS"), exist_ok=True)     # Crear un directorio para guardar los archivos
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        escribir_log(f"{datetime.now()} - No se pudo acceder al directorio para guardar los archivos.")
        sys.exit("Saliendo del programa...")
        
    for enlaceInd in enlaces:
        respuesta = hacer_request_con_reintento(enlaceInd)
        if respuesta is None:
            print(f"No se pudo descargar el archivo {enlaceInd}.")
            escribir_log(f"{datetime.now()} - No se pudo descargar el archivo {enlaceInd}.") # Hacer log de los archivos que no se pudieron descargar
            continue # Si no se puede descargar el archivo, continuar con el siguiente
        else:
            nombre = enlaceInd.split("/")[-1] # Obtener el nombre del archivo
            archivos = os.listdir(os.getenv("PATH_PDFS")) # Obtener los nombres de los archivos que ya se han descargado para no volver a descargarlos
            if nombre in archivos:
                print(f"Archivo {nombre} ya descargado.")
            else:
             with open(f'{os.getenv('PATH_PDFS')}/{nombre}', 'wb') as f:
                f.write(respuesta.content)
                lista_archivos_guardados.append(f'{os.getenv('PATH_PDFS')}/{nombre}')
                print(f"Archivo {nombre} guardado correctamente.")


def receptor_fechas():
    """
    Recibe una solicitud JSON con fechas, las valida, procesa las fechas, registra cualquier error y 
    comienza un hilo para procesar archivos PDF en segundo plano.
    
    :return: Se devuelve una cadena vacía y el código de estado 200.
    """
    data = request.get_json()
    fechas = data["dates"]
    errors = []
    try:
        fechas = validador_fechas(fechas)
        for inicio, fin in fechas:
            fechaOrigen = datetime.strptime(str(inicio), "%Y-%m-%d %H:%M:%S")
            fechaFin = datetime.strptime(str(fin), "%Y-%m-%d %H:%M:%S")
            print(f"Procesando desde {fechaOrigen} hasta {fechaFin}...")
            procesadorInd(fechaOrigen, fechaFin)
    except Exception as e:
        print(f"Error: {e}") # Imprimir la excepción o error en caso de que no se pueda imprimir
        escribir_log(f"{datetime.now()} - Error: {e}")
        errors.append(str(e))
        if errors:
            return "", 500

    hilo_procesar = threading.Thread(target=procesar_documentos, args=(lista_archivos_guardados,))  # Iniciar un hilo para procesar los archivos PDF en segundo plano
    hilo_procesar.start()

    return "", 200


def unir_fechas_solapadas(fechas):
    """
    Toma una lista de intervalos de fechas, fusiona los intervalos solapados y devuelve una lista de intervalos no solapados.
    
    :param fechas: Lista de diccionarios que contienen fechas de inicio y fin como cadenas de texto, las convierte en objetos 
                   datetime y luego fusiona los intervalos de fechas solapados.
    :return intervalosUnidos: Lista de tuplas que representan los intervalos de fechas fusionados sin solapamientos. Cada tupla contiene una 
                              fecha de inicio y una fecha de fin.
    """
    intervalos = []
    for fecha in fechas:   # Convertir las fechas de entrada en objetos datetime y crear Intervalos
        start = datetime.strptime(fecha["start"], "%Y-%m-%d")
        if "end" in fecha:
            end = datetime.strptime(fecha["end"], "%Y-%m-%d")
        else:
            end = start  # Si no se proporciona fecha de fin, considerar como intervalo de un día

        intervalos.append((start, end))

    intervalos.sort() # Ordenar los intervalos por fecha de inicio
    intervalosUnidos = []
    actual_start, actual_end = intervalos[0]
    for intervalo in intervalos[1:]:
        intervalo_start, intervalo_end = intervalo

        if intervalo_start <= actual_end:  # Hay superposición, fusionar los intervalos
            actual_end = max(actual_end, intervalo_end)
        else:
            intervalosUnidos.append((actual_start, actual_end))
            actual_start, actual_end = intervalo_start, intervalo_end

    intervalosUnidos.append((actual_start, actual_end))  # Agregar el último intervalo
    return intervalosUnidos


def validador_fechas(dates):
    """
    Valida una lista de fechas, asegurándose de que las fechas de inicio sean obligatorias, las fechas de fin no sean anteriores a 
    las fechas de inicio y tanto las fechas de inicio como las de fin no estén en el futuro, y luego combina los rangos de fechas superpuestos.
    
    :param dates: Lista de diccionarios que contienen fechas de inicio y fin como cadenas de texto.           
    :return fechas_unidas: Devuelve la lista combinada y validada de fechas después de verificar varias condiciones, como asegurarse de que haya una fecha de inicio,
                           establecer la fecha de fin como la fecha de inicio si no se proporciona, verificar si la fecha de inicio no es posterior a la fecha de fin
                           y asegurarse de que la fecha de inicio y la fecha de fin no estén en el futuro. Luego, la función llama a otra función `unir_fechas_solapadas`
                           para combinar las fechas superpuestas.
    """
    fechas_bruto = []
    for date in dates:
        if "start" not in date:
            raise ValueError("La fecha de inicio es obligatoria.")
        elif date["end"] == "":
            fechas_bruto.append({"start": date["start"], "end": date["start"]})
        elif date["end"] and date["start"] > date["end"]:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        elif date["start"] > datetime.now().strftime("%Y-%m-%d"):
            raise ValueError("La fecha de inicio no puede ser futura.")
        elif date["end"] and date["end"] > datetime.now().strftime("%Y-%m-%d"):
            raise ValueError("La fecha de fin no puede ser futura.")
        else:
            fechas_bruto.append(date)
    fechas_unidas = unir_fechas_solapadas(fechas_bruto)  # Llamamos a la función para combinar las fechas solapadas
    return fechas_unidas


def procesadorInd(fechaOrigen, fechaFin):
    """
    Procesa un rango de fechas para recuperar enlaces de PDF de un sitio web,divide los enlaces en partes iguales y 
    los procesa de forma concurrente utilizando varios hilos.
    
    :param fechaOrigen: La fecha de inicio desde la cual se iniciará el procesamiento. Es un objeto de fecha que 
                        representa la fecha inicial para procesar los documentos.
    :param fechaFin: La fecha de fin hasta la cual desea procesar los datos. Esta función está obteniendo datos 
                     de una URL para cada día a partir de `fechaOrigen` hasta `fechaFin`, extrayendo enlaces de PDF de la respuesta,
    """
    enlaces = {}

    while fechaOrigen <= fechaFin:
        url = f'https://www.boe.es/datosabiertos/api/boe/sumario/{fechaOrigen.strftime("%Y%m%d")}'
        print(f"{url}")
        response = hacer_request_con_reintento(url)
        if response in [401, 404]:
            print(f"El enlace {url} no existe. Pasando al siguiente enlace...")
            # Ir a la siguiente posición en el bucle while
            fechaOrigen += timedelta(days=1)
            continue
        else:
            enlaces = re.findall(r"(?<=>)https:\/\/[\w.\/-]+\.pdf(?=<\/url_pdf>)", response.text)

        print(f"Encontrados {len(enlaces)} documentos del día {fechaOrigen.strftime('%Y-%m-%d')}...")
        fechaOrigen += timedelta(days=1)

        # Haz que los enlaces se dividan en partes los mas iguales posibles
        enlaces_parts = [
            enlaces[i :: int(os.getenv("NUM_HILOS"))]
            for i in range(int(os.getenv("NUM_HILOS")))
        ]

        threads = []
        for i in range(int(os.getenv("NUM_HILOS"))):  # Crear y empezar 5 hilos
            t = threading.Thread(target=procesar_enlaces, args=(enlaces_parts[i],))
            t.start()
            threads.append(t)

        for t in threads: # Esperar a que todos los hilos terminen
            t.join()
