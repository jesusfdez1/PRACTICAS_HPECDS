import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from embedding_function import get_embedding_function
from langchain_community.vectorstores import Chroma
from constants import CHROMA_PATH, PATH_PDFS, CHUNK_SIZE, CHUNK_OVERLAP

def main():
    # Comprueba si la base de datos debe limpiarse (usando el indicador --clear).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Borra la base de datos.")
    args = parser.parse_args()
    if args.reset:
        print("Borrando la base de datos...")
        limpiar_BBDD()

    # Crear (o actualizar) la base de datos.
    documentos = cargar_documentos()
    chunks = dividir_documentos(documentos)
    añadir_a_chroma(chunks)


def cargar_documentos():
    document_loader = PyPDFDirectoryLoader(PATH_PDFS)
    return document_loader.load()


def dividir_documentos(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, #Tamaño máximo de cada fragmento de texto en 800 caracteres. Si el fragmento es mayor a este tamaño, el texto se dividirá en partes más pequeñas.
        chunk_overlap=CHUNK_OVERLAP, #Número de caracteres que se superponen entre fragmentos adyacentes. La superposición ayuda a mantener el contexto entre fragmentos adyacentes
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def añadir_a_chroma(chunks: list[Document]):
    # Carga la base de datos existente.
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())

    # Calcula los IDs de los fragmentos.
    chunks_with_ids = calcular_chunk_ids(chunks)

    # Añade o actualiza los fragmentos en la base de datos.
    existing_items = db.get(include=[])  # IDs siempre se incluyen.
    existing_ids = set(existing_items["ids"])
    print(f"Número de documentos existentes en la base de datos: {len(existing_ids)}")

    # Solo añade los fragmentos que no están en la base de datos.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"Añadiendo {len(new_chunks)} nuevos documentos a la base de datos...")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        
    else:
        print("No hay nuevos documentos para añadir.")


def calcular_chunk_ids(chunks):
    # Esto creará IDs como "pdfs/BOE-A-2019-1.pdf:3:0 donde Fuente : Número de página : Chunk Index
    
    id_ultima_pagina = None
    index_actual_chunk = 0

    for chunk in chunks:
        fuente = chunk.metadata.get("source")
        pagina = chunk.metadata.get("page")
        id_pagina_actual = f"{fuente}:{pagina}"

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

    return chunks


def limpiar_BBDD():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()