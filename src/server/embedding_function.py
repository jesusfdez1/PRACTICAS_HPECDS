from langchain_community.embeddings.ollama import OllamaEmbeddings
from flask import request
import os
import fitz
import datetime
import re
import os
import json
import threading

# Crear un lock global
json_lock = threading.Lock()

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


def get_funcion_embebido() -> OllamaEmbeddings:
    """
    Devuelve una instancia de `OllamaEmbeddings` con un modelo y una URL base específicos.
    
    :return embeddings: Una instancia de la clase OllamaEmbeddings inicializada con los parámetros de modelo y URL base especificados.
    """
    embeddings = OllamaEmbeddings(
        model="joanfm/jina-embeddings-v2-base-es", base_url="http://ollama:11434"
    )
    return embeddings


def set_chunk_values():
    """
    Establece las variables de entorno `CHUNK_SIZE` y `CHUNK_OVERLAP` basándose en los datos JSON recibidos en una solicitud.
    
    :return: Devuelve una cadena vacía y un código de estado HTTP. Si el bloque try tiene éxito, devolverá una cadena vacía y
             un código de estado 200 (indicando éxito). Si ocurre una excepción durante el bloque try, devolverá una cadena vacía y un
             código de estado 500 (indicando un error interno del servidor).
    """
    try:
        datos = request.get_json()
        os.environ["CHUNK_SIZE"] = str(datos["chunkLength"])
        os.environ["CHUNK_OVERLAP"] = str(datos["contextLength"])
    except Exception as e:
        return "", 500
    return "", 200


def get_chunk_values():
    """
    Obtiene los valores de tamaño de fragmento y longitud de contexto.
    
    :return: Devuelve un diccionario con los valores de tamaño de fragmento y longitud de contexto.
    """
    return {
        "chunkLength": int(os.getenv("CHUNK_SIZE")),
        "contextLength": os.getenv("CHUNK_OVERLAP"),
    }, 200


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
