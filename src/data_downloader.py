import sys
import time
import threading 
import requests
import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime
from datetime import timedelta
from flask import Flask
from flask import request
from constants import API_MICROSERVICES_BASE_URL, API_MICROSERVICES_PORT, PATH, PATH_PDFS

app = Flask(__name__)

def escribir_log(mensaje):
    with open(f'{PATH}/log.txt', 'a') as f:
        f.write(f"{mensaje}\n")
    f.close()
    
def controlador_error(response, url):
    error = response.status_code
    root = ET.fromstring(response.content)
    error_message = root.find(".//text").text
    escribir_log(f"{datetime.now()} - Error {error}: '{error_message}' al acceder a la {url}.")

    if error in [401, 404]:
        sys.exit(f"Error {error}: {error_message} Saliendo del programa...")
    elif error == 403:
        sys.exit(f"Error {error}: Acceso no autorizado. Saliendo del programa...")
    elif error in [500, 501, 502, 503]:
        wait_time = 300  # 5 minutos
        print(f"Error {error}: Problema del servidor. Esperando {wait_time / 60} minutos antes de reintentar...")
        time.sleep(wait_time)
    else:
        sys.exit(f"Error inesperado: {error}: {error_message}. Saliendo del programa...")
        
def hacer_request_con_reintento(url, max_intentos=5, delay=350):
    intentos = 0
    response = None  # Inicializar response con None para evitar errores de que no está definido
    if intentos == max_intentos:
        sys.exit(f"Se alcanzó el número máximo de {max_intentos} intentos. Saliendo del programa...")
    while intentos < max_intentos:
        try:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers)
            # Obtener 
            response.raise_for_status()  # Lanzar una excepción para códigos de estado de error
            return response
        except requests.exceptions.RequestException as e:
            if response is not None:
                controlador_error(response, url)
            intentos += 1
            print(f"Reintento {intentos} de {max_intentos} tras error: {e}")
            time.sleep(delay)
    return None


def procesar_enlaces(enlaces):
    #Crear un directorio para guardar los archivos
    try:
        os.makedirs(PATH_PDFS, exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        escribir_log(f"{datetime.now()} - No se pudo acceder al directorio para guardar los archivos.")
        sys.exit("Saliendo del programa...")
    for enlaceInd in enlaces:
        response = hacer_request_con_reintento(enlaceInd)
        if response is None:
            print(f"No se pudo descargar el archivo {enlaceInd}.")
            #Hacer log de los archivos que no se pudieron descargar
            escribir_log(f"{datetime.now()} - No se pudo descargar el archivo {enlaceInd}.")
            # Si no se puede descargar el archivo, continuar con el siguiente
            continue
        else:
            # Obtener el nombre del archivo
            filename = enlaceInd.split("/")[-1]
            #Obtener los nombres de los archivos que ya se han descargado para no volver a descargarlos
            files = os.listdir(PATH_PDFS)
            if filename in files:
                print(f"Archivo {filename} ya descargado.")
            else:
                with open(f'{PATH_PDFS}/{filename}', 'wb') as f:
                    f.write(response.content)
                print(f"Archivo {filename} guardado correctamente.")

def receptor_fechas():
    # Capturar json e imprimir
    #Enviar que se ha recibido la petición correctamente al cliente 200    
    data = request.get_json()
    dates = data["dates"]
    errors = []
    try:
        dates = validador_fechas(dates)
        for inicio, fin in dates:
                fechaOrigen = datetime.strptime(str(inicio), "%Y-%m-%d %H:%M:%S")
                fechaFin = datetime.strptime(str(fin), "%Y-%m-%d %H:%M:%S")
                print(f"Procesando desde {fechaOrigen} hasta {fechaFin}...")
                procesadorInd(fechaOrigen, fechaFin)
    except Exception as e:
            # Imprimir la excepción o error en caso de que no se pueda imprimir
            print(f"Error: {e}")
            escribir_log(f"{datetime.now()} - Error: {e}")
            errors.append(str(e))
    if errors:
            return "Internal Server Error", 500
    return "OK", 200


def merge_overlapping_dates(dates_check):
    intervals = []
    # Convertir las fechas de entrada en objetos datetime y crear Intervalos
    for date in dates_check:
        start = datetime.strptime(date["start"], "%Y-%m-%d")
        if "end" in date:
            end = datetime.strptime(date["end"], "%Y-%m-%d")
        else:
            end = start  # Si no se proporciona fecha de fin, considerar como intervalo de un día

        intervals.append((start, end))

    # Ordenar los intervalos por fecha de inicio
    intervals.sort()

    merged_intervals = []
    current_start, current_end = intervals[0]

    for interval in intervals[1:]:
        interval_start, interval_end = interval

        if interval_start <= current_end:  # Hay superposición, fusionar los intervalos
            current_end = max(current_end, interval_end)
        else:
            merged_intervals.append((current_start, current_end))
            current_start, current_end = interval_start, interval_end

    merged_intervals.append((current_start, current_end))  # Agregar el último intervalo

    return merged_intervals

def validador_fechas(dates):
    dates_check = []
    
    for date in dates:
        if "start" not in date:
            raise ValueError("La fecha de inicio es obligatoria.")
        elif date["end"] == "":
            dates_check.append({"start": date["start"], "end": date["start"]})
        elif date["end"] and date["start"] > date["end"]:
            raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        elif date["start"] > datetime.now().strftime("%Y-%m-%d"):
            raise ValueError("La fecha de inicio no puede ser futura.")
        elif date["end"] and date["end"] > datetime.now().strftime("%Y-%m-%d"):
            raise ValueError("La fecha de fin no puede ser futura.")
        else:
            dates_check.append(date)

    # Llamamos a la función para combinar las fechas solapadas
    merged_dates = merge_overlapping_dates(dates_check)
    return merged_dates

def procesadorInd(fechaOrigen, fechaFin):
    enlaces = {}
    num_hilos=15
         
    while fechaOrigen <= fechaFin:
        url = f'https://www.boe.es/datosabiertos/api/boe/sumario/{fechaOrigen.strftime("%Y%m%d")}'
        print(f"{url}")
        response = hacer_request_con_reintento(url)
        if response is None:
            print("No se encontraron documentos. Saliendo del programa...")
            break
        else:
            # Poner de regex para obtener los enlaces (?<=>)https:\/\/[\w.\/-]+\.pdf(?=<\/url_pdf>)
            enlaces = re.findall(r'(?<=>)https:\/\/[\w.\/-]+\.pdf(?=<\/url_pdf>)', response.text)

        print(f"Encontrados {len(enlaces)} documentos del día {fechaOrigen.strftime('%Y-%m-%d')}...")
        fechaOrigen += timedelta(days=1)

        #Haz que los enlaces se dividan en partes los mas iguales posibles
        enlaces_parts = [enlaces[i::num_hilos] for i in range(num_hilos)]

        # Crear y empezar 5 hilos
        threads = []
        for i in range(num_hilos):
            t = threading.Thread(target=procesar_enlaces, args=(enlaces_parts[i],))
            t.start()
            threads.append(t)

        # Esperar a que todos los hilos terminen
        for t in threads:
            t.join()


    
    