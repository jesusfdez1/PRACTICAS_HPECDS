import os

# CONSTANTES DE RUTAS
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH_PDFS = f'{PATH}/data'
PATH_JSON = f'{PATH_PDFS}/dates.json'
CHROMA_PATH = "chroma"

# CONSTANTES DE API
API_MICROSERVICES_BASE_URL = '0.0.0.0'
API_MICROSERVICES_PORT = 3001


# CONSTANTES DE CHUNKING
CHUNK_SIZE=500
CHUNK_OVERLAP=90


MAX_TOKENS=4096
NUM_HILOS=8
MODEL_LLM ="llama3.1:8b-instruct-q5_K_M"

# CONSTANTES DE PROMPT
PROMPT_TEMPLATE = """
Tu tarea consiste en generar una respuesta para la consulta proporcionada, teniendo en cuenta el contexto histórico especificado. Aquí tienes los detalles necesarios para formular una respuesta coherente y lógica, basándote en la historia y el contexto proporcionados:

Interacciones históricas: {historial}
Contexto proporcionado: {context}
Pregunta actual del usuario: {question}
Asegúrate de que tu respuesta sea comprensible y relevante, utilizando la información del historial de mensajes y el contexto para ofrecer una respuesta completa.  Solo puedes decir al usuario tu respuesta, no hagas referencia a nada más.
"""

NO_CONTEXT_PROMPT_TEMPLATE = """
Tu tarea consiste en generar una respuesta para la consulta proporcionada, teniendo en cuenta el contexto histórico especificado. Aquí tienes los detalles necesarios para formular una respuesta coherente y lógica, basándote en la historia y el contexto proporcionados:

Interacciones históricas: {historial}
Pregunta actual del usuario: {question}
Asegúrate de que tu respuesta sea comprensible y relevante, utilizando la información del historial de mensajes.  Solo puedes decir al usuario tu respuesta, no hagas referencia a nada más.
"""

NO_CONTEXT_HISTORIAL_PROMPT_TEMPLATE = """
Tu tarea consiste en generar una respuesta para la consulta proporcionada. Aquí tienes los detalles necesarios para formular una respuesta coherente y lógica:

Pregunta actual del usuario: {question}
Asegúrate de que tu respuesta sea comprensible y relevante.
"""
