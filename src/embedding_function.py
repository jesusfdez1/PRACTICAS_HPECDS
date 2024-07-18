#from langchain_community.embeddings.bedrock import BedrockEmbeddings #No se puede usar en local. Comentar la siguiente y descomentar esta para usar en AWS
from langchain_community.embeddings.ollama import OllamaEmbeddings


def get_embedding_function():
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    return embeddings

# embeddings = BedrockEmbeddings( credentials_profile_name="default", region_name="us-east-1")  #Mejores resultados en AWS pero no se puede usar en local