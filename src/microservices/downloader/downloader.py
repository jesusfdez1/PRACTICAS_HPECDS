from flask import request,Flask
import fitz
import sys
import time
import threading
import requests
import xml.etree.ElementTree as ET
import re
import os
import json
from datetime import datetime
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings.ollama import OllamaEmbeddings
from waitress import serve
from flask_cors import CORS

global lista_archivos_guardados
lista_archivos_guardados = []
json_lock = threading.Lock()


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

def procesar_documentos(archivos):
    chunks = cargar_documentos_paralelo(archivos)
    añadir_chroma(chunks)

def cargar_documentos_paralelo(rutas_archivos):
    """
    Carga varios documentos en paralelo utilizando un ThreadPoolExecutor y un separador de texto.
    
    :param rutas_archivos: Lista de rutas de archivos. Esta función carga y procesa documentos en paralelo a partir de
                           las rutas de archivos especificadas.
    :return chunks: Lista de fragmentos de documentos que se han cargado en paralelo a partir de la lista de rutas de archivos proporcionada.
    """
    chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(os.getenv("CHUNK_SIZE")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP")),
        length_function=len,
        is_separator_regex=False,
    )
    if not isinstance(rutas_archivos, list):
        raise TypeError("Se esperaba una lista de rutas de archivos")
    with ThreadPoolExecutor(max_workers=int(int(os.getenv("NUM_HILOS")))) as executor:
        futures = []
        for ruta in rutas_archivos:
            futures.append(executor.submit(cargar_documento, ruta, text_splitter))

        for future in as_completed(futures):
            try:
                docs = future.result()
                chunks.extend(docs)
            except Exception as e:
                print(f"Error al procesar archivo: {e}")
    return chunks

def cargar_documento(ruta, text_splitter):
    """
    Carga un documento PDF desde una ruta especificada, divide su contenido utilizando
    un separador de texto, procesa el contenido reemplazando los caracteres de salto de línea y los espacios dobles, agrega
    metadatos con la fecha del documento si está disponible, y devuelve una lista de documentos procesados.
    
    :param ruta: Ruta del archivo que se va a cargar y procesar.
    :param text_splitter: Un parámetro utilizado para dividir el contenido de texto de un documento en fragmentos o 
                          segmentos más pequeños.
    :return docs: Una lista de documentos después de procesar el archivo de entrada
                  ubicado en la ruta especificada por `ruta`. Si no se encuentra el archivo, se devuelve una lista vacía. Si hay
                  un error durante el procesamiento, se imprime un mensaje de error y también se devuelve una lista vacía.
    """
    try:
        fecha = get_fecha_individual(ruta)
        docs = PyPDFLoader(ruta).load_and_split(text_splitter)
        for doc in docs:
            doc.page_content = doc.page_content.replace("\n", " ").replace("  ", " ")
            if fecha is not None:
                doc.metadata["date"] = fecha.strftime("%d/%m/%Y")
        return docs
    except FileNotFoundError:
        print(f"El archivo {ruta} no se encontró.")
        return []
    except Exception as e:
        print(f"Error al procesar el archivo {ruta}: {e}")
        return []


def añadir_chroma(chunks):
    """
    Añade fragmentos a la base de datos de Chroma si aún no están presentes.
    
    :param chunks: Lista de fragmentos que se van a añadir a la base de datos.
    """
    db = Chroma(
        persist_directory=os.getenv("CHROMA_PATH"),
        embedding_function=get_funcion_embebido(),
    )
    chunks_con_ids = calcular_chunk_ids(chunks)
    items_existentes = db.get(include=[])
    ids_existentes = set(items_existentes["ids"])
    print(f"Número de documentos existentes en la base de datos: {len(ids_existentes)}")

    nuevos_chunks = [chunk for chunk in chunks_con_ids if chunk.metadata["id"] not in ids_existentes]

    if len(nuevos_chunks) > 0:
        print(f"Añadiendo {len(nuevos_chunks)} nuevos documentos a la base de datos...")
        new_chunk_ids = [chunk.metadata["id"] for chunk in nuevos_chunks]
        db.add_documents(nuevos_chunks, ids=new_chunk_ids)
        print(f"Base de datos actualizada con éxito. Número total de documentos: {len(ids_existentes) + len(nuevos_chunks)}")
    else:
        print("No hay nuevos documentos para añadir.")


def calcular_chunk_ids(chunks):
    """
    Asigna IDs únicos a los chunks basados en la información de sus metadatos.
    
    :param chunks: Toma una lista de `chunks` como entrada. Se espera que cada chunk en la lista tenga 
                   metadatos que contengan información sobre la fuente y la página a la que pertenece. 
                   La función calcula un ID único para cada chunk basado en el nombre del archivo fuente, 
                   el número de página y un índice para diferenciarlos.
    :return chunks: Devuelve la lista de `chunks` actualizada, donde cada chunk incluye un nuevo campo de metadatos 
                    "id" que se calcula en función del nombre del archivo fuente, el número de página y un índice para cada página.
    """
    id_ultima_pagina = None
    index_actual_chunk = 0
    for chunk in chunks:
        fuente = chunk.metadata.get("source")
        try:
            nombre = os.path.basename(fuente)
        except:
            nombre = fuente

        pagina = chunk.metadata.get("page")
        id_pagina_actual = f"{nombre}:{pagina}"

        if id_pagina_actual == id_ultima_pagina:
            index_actual_chunk += 1
        else:
            index_actual_chunk = 0

        chunk_id = f"{id_pagina_actual}:{index_actual_chunk}"
        id_ultima_pagina = id_pagina_actual

        chunk.metadata["id"] = chunk_id
    return chunks



def get_funcion_embebido() -> OllamaEmbeddings:
    """
    Devuelve una instancia de `OllamaEmbeddings` con un modelo y una URL base específicos.
    
    :return embeddings: Una instancia de la clase OllamaEmbeddings inicializada con los parámetros de modelo y URL base especificados.
    """
    embeddings = OllamaEmbeddings(
        model="joanfm/jina-embeddings-v2-base-es", base_url="http://ollama:11434"
    )
    return embeddings



def get_fecha_individual(archivo):
    """
    Lee los metadatos de un archivo PDF, extrae las palabras clave, intenta convertir la última palabra clave 
    a un formato de fecha y guarda la fecha en un archivo JSON.
    
    :param archivo: Representa el nombre del archivo PDF que necesita ser procesado.
    :return ultima_fecha / fecha_alternativa: Devuelve el valor de fecha parseado si puede convertir con éxito 
             la última palabra clave en los metadatos del PDF a un formato de fecha, o un valor de fecha alternativo 
             obtenido de otra palabra clave si la conversión falla. Si ambos intentos fallan, devuelve `None`.
    """
    ruta_archivo = os.path.join(os.getenv("PATH_PDFS"), archivo)
    if os.path.isfile(ruta_archivo) and archivo.lower().endswith(".pdf"):
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
                    guardar_fecha_json(archivo, ultima_fecha)
                    return ultima_fecha
                except ValueError:
                    # Si no se puede convertir, intentar con otro valor
                    ultimo_valor = palabras_clave.split(";")[3].strip()
                    fecha_alternativa = get_fecha_desde_texto(ultimo_valor)
                    if fecha_alternativa:
                        # Guardar la fecha en el archivo JSON
                        guardar_fecha_json(archivo, fecha_alternativa)
                    return fecha_alternativa
        except Exception as e:
            print(f"Error al procesar archivo {archivo}: {e}")
            pass


def guardar_fecha_json(archivo, fecha):
    """
    Guarda o actualiza una fecha asociada a un archivo en un archivo JSON.
    
    :param archivo: Cadena que representa la ruta del archivo donde deseas guardar la información de 
                    la fecha en formato JSON. Esta función lee los datos existentes de un archivo JSON, actualiza o 
                    agrega una nueva entrada de fecha basada en la `fecha` proporcionada (objeto de fecha).
    
    :param fecha: Objeto de fecha que representa la fecha que deseas guardar en el archivo JSON. Se 
                  formatea utilizando el método `strftime` con el formato `"%d/%m/%Y"`, que representa la fecha 
                  en el formato día/mes/año.
    """
    # Leer datos existentes del archivo JSON
    with json_lock:
        if os.path.exists(os.getenv("PATH_JSON")):
            with open(os.getenv("PATH_JSON"), "r") as archivo_json:
                datos = json.load(archivo_json)
        else:
            datos = {}

        nombre_base_archivo = os.path.basename(archivo)
        fecha_formateada = fecha.strftime("%d/%m/%Y")
        # Actualizar o agregar la fecha en el diccionario
        datos[nombre_base_archivo] = fecha_formateada

        # Guardar el diccionario actualizado en el archivo JSON
        with open(os.getenv("PATH_JSON"), "w") as archivo_json:
            json.dump(datos, archivo_json, indent=4)
        print(
            f"Fecha del archivo '{nombre_base_archivo}' guardada/actualizada en el archivo JSON."
        )


def get_fecha_desde_texto(texto):
    """
    Extrae una fecha de un texto dado en formato español.

    :param texto: Toma un texto de entrada y extrae una fecha de él.  El patrón de expresión regular `patron_fecha`
                  se utiliza para buscar una fecha en el formato "día_de_la_semana día de mes de año".
    :return datetime: Se devuelve un objeto `datetime` que representa la fecha extraída del texto de entrada.
    """
    patron_fecha = r"(?P<dia_semana>\w+)\s+(?P<dia>\d{1,2})\s+de\s+(?P<mes>\w+)\s+de\s+(?P<anio>\d{4})\s*"
    coincidencia_fecha = re.search(patron_fecha, texto, re.IGNORECASE)

    if coincidencia_fecha:
        dia = int(coincidencia_fecha.group("dia"))
        mes_str = coincidencia_fecha.group("mes").lower()
        anio = int(coincidencia_fecha.group("anio"))

        meses = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "octubre": 10,
            "noviembre": 11,
            "diciembre": 12,
        }
        mes = meses.get(mes_str)

        if mes:
            return datetime.datetime(anio, mes, dia)



app = Flask(__name__)
CORS(app)

# Ruta para el importador de datos
app.route("/downloader", methods=["POST"])(receptor_fechas)

if __name__ == "__main__":
    serve(app, host=os.getenv('DOWNLOADER'), port=int(os.getenv('DOWNLOADER_PORT')))