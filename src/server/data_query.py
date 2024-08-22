from flask import request, jsonify, Response
from datetime import datetime
import json
from collections import deque
import time
from threading import Lock
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from embedding_function import get_embedding_function
from constants import CHROMA_PATH, PROMPT_TEMPLATE, MODEL_LLM, NO_CONTEXT_PROMPT_TEMPLATE, NO_CONTEXT_HISTORIAL_PROMPT_TEMPLATE, MAX_TOKENS

lock = Lock()

def generar_titulo():
    try:
        data = request.data.decode('utf-8')
        # Convertir los datos de texto JSON a un diccionario de Python
        json_data = json.loads(data)
        # Obtener la lista de mensajes del diccionario
        messages = json_data.get('prompt', [])
        # Enviar prompt a Ollama
        model = Ollama(model=MODEL_LLM, base_url="http://ollama:11434")
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
        historial = deque()

        # Encontrar el contenido del usuario más reciente      
        latest_user_content = next((message["content"] for message in reversed(messages) if message["role"] == "user"), None)
        date = next((message["date"] for message in reversed(messages) if message["role"] == "user"), None)
        #Si hay mas mensajes, obtener el contenido del usuario y del asistnente de los mensajes anteriores y concatenarlos
        if len(messages) > 1:
            for i in range(len(messages)-2):
                if messages[i]["role"] == "assistant":
                    historial.append("Contestación del asistente LLM: " + messages[i]["content"])
                elif messages[i]["role"] == "user":
                    historial.append("Contestación del usuario: " + messages[i]["content"])         

        global continuar
        if latest_user_content:
          print("Latest user content:", latest_user_content)
          print("Date:", date)
          print("Historial:", historial)
          with lock:
            continuar = True
            return query_rag(latest_user_content,date, historial)
        else:
          with lock:
             continuar = False          
             return '', 204  # Retornar un estado 204 (No Content)

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})


    # Function to format prompt based on conditions
def format_prompt(results, query_text, historial):
        if historial == "" and not results:
            prompt_template = ChatPromptTemplate.from_template(NO_CONTEXT_HISTORIAL_PROMPT_TEMPLATE)
            return prompt_template.format(question=query_text)
        elif not results:
            prompt_template = ChatPromptTemplate.from_template(NO_CONTEXT_PROMPT_TEMPLATE)
            return prompt_template.format(question=query_text, historial=historial)
        else:
            context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
            prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
            return prompt_template.format(context=context_text, question=query_text, historial=historial)
        
def query_rag(query_text, date, historial):
    start_time_total = time.time()
    load_duration = 0
    prompt_eval_count = 0
    prompt_eval_duration = 0
    eval_count = 0
    eval_duration = 0
    try:
        # Prepare the DB.
        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        # Search the DB.
        results = db.similarity_search_with_score(query_text, k=7, filter={"date": date})

        start_time_load = time.time()
        model = Ollama(model=MODEL_LLM, num_ctx=MAX_TOKENS, base_url="http://ollama:11434")
        print(model.base_url)
        load_duration = (time.time() - start_time_load) * 1000000
    except Exception as e:
            print(f"Error en query_rag: {str(e)}")
            return jsonify({"error": f"Error en query_rag: {str(e)}"})

    while True:
        # Format prompt with current historial and results
        prompt = format_prompt(results, query_text, "\n".join(historial))

        # Check prompt size after formatting
        if model.get_num_tokens(prompt) <= MAX_TOKENS:
            break  # Exit loop if prompt size is within limit

        # Reduce historial until prompt size is within limit
        if historial:
             # Remove first element from historial
            historial.popleft()
        else:
            # If historial is empty, break the loop to avoid infinite loop
            break

    print(prompt)
    #Calcular 

    try:
            # Prepare the headers for streaming NDJSON
        def generate_ndjson():
            nonlocal prompt_eval_count, prompt_eval_duration, eval_count, eval_duration

            for chunk in model.astream(prompt):
                # Mide el tiempo de evaluación del prompt
                start_time_prompt_eval = time.time()

                with lock:
                    if continuar:
                        created_at = datetime.now().isoformat() + "Z"
                        yield json.dumps({
                            "created_at": created_at,
                            "message": {
                                "role": "assistant",
                                "content": chunk
                            },
                            "done": False
                        }) + '\n'
                    else:
                        break
                
            if results:
                #Obtener el origen de los documentos
                sources = [doc.metadata.get("id", None) for doc, _score in sorted(results, key=lambda x: x[0].metadata.get("id", "").lower())]
        
                #Concatenar los orígenes de los documentos en una cadena
                formatted_response = f"\n\n***Fuentes utilizadas:***\n"
                formatted_response += "\n".join([f"- **Archivo:** {source.split(':')[0]} | **Número de página:** {int(source.split(':')[1]) + 1} - **Fragmento:** {int(source.split(':')[2]) + 1}" for source in sources])
                yield json.dumps({
                            "created_at": created_at,
                            "message": {
                                "role": "assistant",
                                "content": formatted_response
                            },
                            "done": False
                        }) + '\n'

                # Incrementa el contador de evaluaciones del prompt
                prompt_eval_count += 1

                # Incrementa el tiempo total de evaluación del prompt
                prompt_eval_duration += (time.time() - start_time_prompt_eval) * 1000000  # En microsegundos

                # Mide el tiempo de evaluación general
                start_time_eval = time.time()
                
                # Añadir cualquier otra operación que se quiera medir en eval_duration
                # eval_duration += (time.time() - start_time_eval) * 1000000
                # eval_count += 1
                eval_duration += (time.time() - start_time_eval) * 1000000  # En microsegundos

            # Genera el NDJSON final con las métricas
            yield json.dumps({
                "created_at": datetime.now().isoformat() + "Z",
                "message": {
                    "role": "assistant",
                    "content":  ""
                },
                "done_reason": "stop",
                "done": True,
                "total_duration": (time.time() - start_time_total) * 1000000,  
                "load_duration": load_duration,
                "prompt_eval_count": prompt_eval_count,
                "prompt_eval_duration": prompt_eval_duration,
                "eval_count": eval_count,
                "eval_duration": eval_duration
            }) + '\n'

            # Return the response as NDJSON
            return Response(generate_ndjson(), mimetype='application/x-ndjson')
        
    except Exception as e:
            print(f"Error en query_rag: {str(e)}")
            return jsonify({"error": f"Error en query_rag 2: {str(e)}"})