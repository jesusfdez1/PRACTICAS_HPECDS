import os

# CONSTANTES DE RUTAS
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_PDFS = f'{PATH}/pdfs'
CHROMA_PATH = "chroma"

# CONSTANTES DE API
API_MICROSERVICES_BASE_URL = 'localhost'
API_MICROSERVICES_PORT = 3001


# CONSTANTES DE CHUNKING
CHUNK_SIZE=500
CHUNK_OVERLAP=90


NUM_HILOS=8
MODEL_LLM ="llama3.1:8b-instruct-q8_0"

# CONSTANTES DE PROMPT
PROMPT_TEMPLATE = """
Responde la siguiente pregunta basándote únicamente en el siguiente contexto:
{context}

---
Responde la pregunta basándote en el contexto anterior: {question}
"""