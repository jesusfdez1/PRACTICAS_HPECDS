import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from embedding_function import get_funcion_embebido, get_fecha_individual
from langchain_chroma import Chroma


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


def limpiar_chroma():
    """
    Intenta eliminar una colección de Chroma y un archivo JSON si existen, devolviendo un código de estado de éxito o error.
    
    :return: Una cadena vacía y un código de estado de 200 si la función se ejecuta correctamente. Si ocurre una excepción,
             se devuelve una cadena vacía y un código de estado de 500.
    """
    try:
        if os.path.exists(os.getenv("CHROMA_PATH")):
            db = Chroma(persist_directory=os.getenv("CHROMA_PATH"))
            db.delete_collection()
        # Si existe el archivo os.getenv('PATH_JSON'))
        if os.path.isfile(os.getenv("PATH_JSON")):
            os.remove(os.getenv("PATH_JSON"))
        return "", 200
    except Exception as e:
        return "", 500
