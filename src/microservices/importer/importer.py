from flask import request, Flask
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.ollama import OllamaEmbeddings
import fitz
import datetime
import re
import json
from langchain_chroma import Chroma
from waitress import serve
from flask_cors import CORS

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


app = Flask(__name__)
CORS(app)

# Ruta para el importador de datos
app.route("/importer", methods=["POST"])(importar_archivos) 

if __name__ == "__main__":
    serve(app, host=os.getenv('IMPORTER'), port=int(os.getenv('IMPORTER_PORT')))