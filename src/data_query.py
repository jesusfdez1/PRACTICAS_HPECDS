from flask import request, jsonify, Response
from datetime import datetime
import json
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from embedding_function import get_embedding_function
from constants import CHROMA_PATH, PROMPT_TEMPLATE, MODEL_LLM


def generate_title():
    try:
        data = request.data.decode('utf-8')
        # Convertir los datos de texto JSON a un diccionario de Python
        json_data = json.loads(data)
        # Obtener la lista de mensajes del diccionario
        messages = json_data.get('prompt', [])
        # Enviar prompt a Ollama
        model = Ollama(model=MODEL_LLM)
        response_text = model.invoke(messages)
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"response": "Chat del " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

def procesar_peticion():
    try:
        # Leer los datos de la solicitud directamente
        data = request.data.decode('utf-8')
        # Convertir los datos de texto JSON a un diccionario de Python
        json_data = json.loads(data)
        
        # Obtener la lista de mensajes del diccionario
        messages = json_data.get('messages', [])
        
        # Encontrar el contenido del usuario más reciente      
        latest_user_content = next((message["content"] for message in reversed(messages) if message["role"] == "user"), None)
        
        if latest_user_content:
            print("Latest user content:", latest_user_content)
            return query_rag(latest_user_content)
        
        return jsonify({"response": "No se ha recibido ninguna pregunta"})
    
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})


def query_rag(query_text: str):
    # Prepare the DB.
    # embedding_function = get_embedding_function()
    # db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # # Search the DB.
    # results = db.similarity_search_with_score(query_text, k=5)

    # context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    # prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    # prompt = prompt_template.format(context=context_text, question=query_text)
    # # print(prompt)

    try:
            model = Ollama(model=MODEL_LLM)
            
            # Prepare the headers for streaming NDJSON
            def generate_ndjson():
                for chunk in model.stream(query_text):
                    created_at = datetime.now().isoformat() + "Z"
                    yield json.dumps({
                        "created_at": created_at,
                        "message": {
                            "role": "assistant",
                            "content": chunk
                        },
                        "done": False
                    }) + '\n'
                
                # Final chunk to indicate completion
                yield json.dumps({
                    "created_at": created_at,
                    "message": {
                        "role": "assistant",
                        "content": ""
                    },
                    "done_reason": "stop",
                    "done": True,
                    "total_duration": 0,
                    "load_duration": 0,
                    "prompt_eval_count": 0,
                    "prompt_eval_duration": 0,
                    "eval_count": 0,
                    "eval_duration": 0
                }) + '\n'

            # Return the response as NDJSON
            return Response(generate_ndjson(), mimetype='application/x-ndjson')
        #sources = [doc.metadata.get("id", None) for doc, _score in results]
        #formatted_response = f"Response: {response_text}\nSources: {sources}"
        #print(formatted_response)
        
    except Exception as e:
            print(f"Error in query_rag: {str(e)}")
            return jsonify({"error": f"Error in query_rag: {str(e)}"})
 


