import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from embedding_function import get_embedding_function, obtener_fecha_individual
from langchain_community.vectorstores import Chroma
from constants import CHROMA_PATH, PATH_PDFS, CHUNK_SIZE, CHUNK_OVERLAP

def procesar_documentos(archivos):
    chunks = cargar_documentos(archivos)  # Crear (o actualizar) la base de datos.
    añadir_a_chroma(chunks)

def cargar_documentos(rutas_archivos):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, #Tamaño máximo de cada fragmento de texto en 800 caracteres. Si el fragmento es mayor a este tamaño, el texto se dividirá en partes más pequeñas.
        chunk_overlap=CHUNK_OVERLAP, #Número de caracteres que se superponen entre fragmentos adyacentes. La superposición ayuda a mantener el contexto entre fragmentos adyacentes
        length_function=len,
        is_separator_regex=False,
    )
    if not isinstance(rutas_archivos, list):
        raise TypeError("Se esperaba una lista de rutas de archivos")
    all_documents = []
    for ruta in rutas_archivos:
        try:
                pdf_reader =  PyPDFLoader(ruta).load_and_split(text_splitter)
                all_documents.extend(pdf_reader)
        except FileNotFoundError:
            print(f"El archivo {ruta} no se encontró.")
        except Exception as e:
            print(f"Error al procesar el archivo {ruta}: {e}")
    return all_documents

def añadir_a_chroma(chunks: list[Document]):
    # Carga la base de datos existente.
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())   

    # Calcula los IDs de los fragmentos.
    chunks_con_ids = calcular_chunk_ids(chunks)
    print(chunks_con_ids)
    # Añade o actualiza los fragmentos en la base de datos.
    items_existentes = db.get(include=[])  # IDs siempre se incluyen.
    ids_existentes = set(items_existentes["ids"])
    print(f"Número de documentos existentes en la base de datos: {len(ids_existentes)}")

    # Solo añade los fragmentos que no están en la base de datos.
    new_chunks = []
    for chunk in chunks_con_ids:
        if chunk.metadata["id"] not in ids_existentes:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"Añadiendo {len(new_chunks)} nuevos documentos a la base de datos...")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        
        print(f"Base de datos actualizada con éxito. Número total de documentos: {len(ids_existentes) + len(new_chunks)}")
    else:
        print("No hay nuevos documentos para añadir.")


def calcular_chunk_ids(chunks):
    # Esto creará IDs como "pdfs/BOE-A-2019-1.pdf:3:0 donde Fuente : Número de página : Chunk Index
    id_ultima_pagina = None
    index_actual_chunk = 0

    for chunk in chunks:
        fuente = chunk.metadata.get("source")
        #Guardar en fuente el nombre del archivo
        try:
            nombre = os.path.basename(fuente)
        except:
            nombre = fuente

        pagina = chunk.metadata.get("page")
        id_pagina_actual = f"{nombre}:{pagina}"
        # Si el ID de la página es el mismo que el anterior, incrementa el índice.
        if id_pagina_actual == id_ultima_pagina:
            index_actual_chunk += 1
        else:
            index_actual_chunk = 0

        # Calcula el ID del chunk.
        chunk_id = f"{id_pagina_actual}:{index_actual_chunk}"
        id_ultima_pagina = id_pagina_actual

        # Esto añade el ID del chunk a los metadatos de la página.
        chunk.metadata["id"] = chunk_id
        chunk.metadata["date"] = obtener_fecha_individual(fuente).strftime("%d/%m/%Y")
    return chunks

def limpiar_BBDD():
    try:
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH)
        return "", 200
    except Exception as e:
        return "", 500

