from flask import request, jsonify
import json
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from embedding_function import get_embedding_function
from constants import CHROMA_PATH, PROMPT_TEMPLATE


def procesar_peticion():
    if request.headers.get('Content-Type') == 'text/event-stream':
        # Leer los datos de la solicitud directamente
        data = request.data.decode('utf-8')
        # Convertir los datos de texto JSON a un diccionario de Python
        json_data = json.loads(data)
        
        # Obtener la lista de mensajes del diccionario
        messages = json_data.get('messages', [])
        
        # Encontrar el contenido del usuario más reciente
        latest_user_content = None
        for message in reversed(messages):
            if message["role"] == "user":
                latest_user_content = message["content"]
                break
        
        # Imprimir el contenido del usuario más reciente
        print("Contenido del usuario más reciente:", latest_user_content)
    
#query_rag(query_text)


def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    # print(prompt)

    model = Ollama(model="mistral")
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)
    return response_text