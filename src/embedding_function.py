#from langchain_community.embeddings.bedrock import BedrockEmbeddings #No se puede usar en local. Comentar la siguiente y descomentar esta para usar en AWS
from langchain_community.embeddings.ollama import OllamaEmbeddings
from flask import request


def get_embedding_function():
   # embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    embeddings = OllamaEmbeddings(model="joanfm/jina-embeddings-v2-base-es")
    return embeddings

# embeddings = BedrockEmbeddings( credentials_profile_name="default", region_name="us-east-1")  #Mejores resultados en AWS pero no se puede usar en local

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