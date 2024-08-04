from langchain_community.embeddings.ollama import OllamaEmbeddings
from flask import request
from constants import CHUNK_SIZE, CHUNK_OVERLAP

def get_embedding_function():
   # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    embeddings = OllamaEmbeddings(model="joanfm/jina-embeddings-v2-base-es")
    return embeddings

def set_chunk_values():
    global CHUNK_SIZE
    global CHUNK_OVERLAP
    try:
        data = request.get_json()
        size = data["chunkLength"]
        overlap = data["contextLength"]
        CHUNK_SIZE = size
        CHUNK_OVERLAP = overlap
    except Exception as e:
        return "Internal Server Error", 500
    return "OK", 200

def get_chunk_values():
    return {"chunkLength": CHUNK_SIZE, "contextLength": CHUNK_OVERLAP}, 200