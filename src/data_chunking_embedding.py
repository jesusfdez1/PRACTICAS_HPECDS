import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from embedding_function import get_embedding_function
from langchain_community.vectorstores import Chroma


CHROMA_PATH = "chroma"
DATA_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/pdfs"


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
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()


def dividir_documentos(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=780, #Tamaño máximo de cada fragmento de texto en 800 caracteres. Si el fragmento es mayor a este tamaño, el texto se dividirá en partes más pequeñas.
        chunk_overlap=90, #Número de caracteres que se superponen entre fragmentos adyacentes. La superposición ayuda a mantener el contexto entre fragmentos adyacentes
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def añadir_a_chroma(chunks: list[Document]):
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

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

    # This will create IDs like "pdfs/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks


def limpiar_BBDD():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()