import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from embedding_function import get_embedding_function, obtener_fecha_individual
from langchain_chroma import Chroma
from constants import CHROMA_PATH, CHUNK_SIZE, CHUNK_OVERLAP, NUM_HILOS

def procesar_documentos(archivos):
    chunks = cargar_documentos_paralelo(archivos)  # Cargar documentos de manera paralela.
    añadir_a_chroma(chunks)

def cargar_documentos_paralelo(rutas_archivos):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    if not isinstance(rutas_archivos, list):
        raise TypeError("Se esperaba una lista de rutas de archivos")

    chunks = []

    with ThreadPoolExecutor(max_workers=NUM_HILOS) as executor:
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
    try:
        fecha = obtener_fecha_individual(ruta)
        docs = PyPDFLoader(ruta).load_and_split(text_splitter)
        for doc in docs:
            doc.page_content = doc.page_content.replace('\n', ' ').replace('  ', ' ')
            if fecha is not None:
                 doc.metadata["date"] = fecha.strftime("%d/%m/%Y")
        return docs
    except FileNotFoundError:
        print(f"El archivo {ruta} no se encontró.")
        return []
    except Exception as e:
        print(f"Error al procesar el archivo {ruta}: {e}")
        return []

def añadir_a_chroma(chunks):
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())
    chunks_con_ids = calcular_chunk_ids(chunks)
    print(chunks_con_ids)
    
    items_existentes = db.get(include=[])
    ids_existentes = set(items_existentes["ids"])
    print(f"Número de documentos existentes en la base de datos: {len(ids_existentes)}")

    new_chunks = [chunk for chunk in chunks_con_ids if chunk.metadata["id"] not in ids_existentes]

    if len(new_chunks) > 0:
        print(f"Añadiendo {len(new_chunks)} nuevos documentos a la base de datos...")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        print(f"Base de datos actualizada con éxito. Número total de documentos: {len(ids_existentes) + len(new_chunks)}")
    else:
        print("No hay nuevos documentos para añadir.")

def calcular_chunk_ids(chunks):
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

def limpiar_BBDD():
    try:
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
        return "", 200
    except Exception as e:
        return "", 500
