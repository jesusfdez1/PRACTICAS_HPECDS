from flask import request, jsonify, Response
from datetime import datetime
import json
from collections import deque
import time
from threading import Lock
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from embedding_function import get_funcion_embebido
import os

lock = Lock()

def formatear_prompt(resultados, query_text, historial):
    """
    Genera un prompt para formular una respuesta coherente basada en las interacciones 
    históricas y el contexto proporcionado, adaptado a diferentes escenarios.
    
    :param resultados: Lista de tuplas donde cada tupla contiene un documento y su puntuación correspondiente. 
                       El documento representa el contenido de una página relacionada con la consulta, y la puntuación indica 
                       la relevancia de ese documento para la consulta.
    :param query_text: Texto de la consulta o pregunta actual del usuario que necesita una respuesta. Se utiliza como 
                       entrada para generar una respuesta relevante y coherente basada en el contexto histórico proporcionado 
                       y cualquier resultado de búsqueda.
    :param historial: Representa las interacciones o mensajes históricos que han ocurrido antes de la consulta 
                      actual. Proporciona contexto para generar una respuesta coherente y lógica a la consulta del usuario. Este 
                      contexto histórico ayuda a asegurar que la respuesta sea relevante y significativa en función del pasado.
    :return: Devuelve un prompt formateado que puede incluir el contexto histórico, el contexto actual y la pregunta.
    """
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
    if historial == "" and not resultados:
        plantilla_prompt = ChatPromptTemplate.from_template(
            NO_CONTEXT_HISTORIAL_PROMPT_TEMPLATE
        )
        return plantilla_prompt.format(question=query_text)
    elif not resultados:
        plantilla_prompt = ChatPromptTemplate.from_template(NO_CONTEXT_PROMPT_TEMPLATE)
        return plantilla_prompt.format(question=query_text, historial=historial)
    else:
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in resultados])
        plantilla_prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        return plantilla_prompt.format(context=context_text, question=query_text, historial=historial)

def generar_titulo():
    """
    Toma los datos JSON, extrae los mensajes, los envía a un modelo de Ollama y devuelve el 
    texto de respuesta o un mensaje de chat predeterminado con la fecha y hora actual si ocurre una excepción.
    
    :return json: Devuelve una respuesta JSON que contiene el texto de respuesta generado por el modelo 
                  de Ollama basado en los mensajes de entrada del prompt, o una respuesta predeterminada si ocurre una 
                  excepción durante el proceso. La respuesta incluye el texto generado o un mensaje con marca de tiempo 
                  si ocurre un error.
    """
    try:
        datos = request.data.decode("utf-8")
        datosJSON = json.loads(datos) # Convertir los datos de texto JSON a un diccionario de Python
        mensajes = datosJSON.get("prompt", [])  # Obtener la lista de mensajes del diccionario
        modelo = Ollama(model=os.getenv("MODEL_LLM")) # Enviar prompt a Ollama
        respuesta = modelo.invoke(mensajes)
        return jsonify({"response": respuesta})
    except Exception as e:
        return jsonify(
            {"response": "Chat del " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        )


def procesar_peticion():
    """
    Procesa una solicitud extrayendo y analizando los datos JSON para determinar el contenido 
    más reciente del usuario y responder en consecuencia.
    
    :return: Devuelve el resultado de la llamada a la función `peticion_rag` con ciertos parámetros, 
    o una cadena vacía con el código de estado 204 (No Content) según las condiciones dentro de la función. 
    Si ocurre una excepción durante el procesamiento, devuelve una respuesta JSON que indica el mensaje de error.
    """
    try:
        # Leer los datos de la solicitud directamente
        data = request.data.decode("utf-8")
        # Convertir los datos de texto JSON a un diccionario de Python
        datosJSON = json.loads(data)

        # Obtener la lista de mensajes del diccionario
        mensajes = datosJSON.get("messages", [])
        historial = deque()

        # Encontrar el contenido del usuario más reciente
        ultimo_contenido_user = next(
            (
                mensaje["content"]
                for mensaje in reversed(mensajes)
                if mensaje["role"] == "user"
            ),
            None,
        )
        fecha = next(
            (
                mensaje["date"]
                for mensaje in reversed(mensajes)
                if mensaje["role"] == "user"
            ),
            None,
        )
        # Si hay mas mensajes, obtener el contenido del usuario y del asistnente de los mensajes anteriores y concatenarlos
        if len(mensajes) > 1:
            for i in range(len(mensajes) - 2):
                if mensajes[i]["role"] == "assistant":
                    historial.append(
                        "Contestación del asistente LLM: " + mensajes[i]["content"]
                    )
                elif mensajes[i]["role"] == "user":
                     historial.append(
                        "Contestación del usuario: " + mensajes[i]["content"]
                    )

        global continuar
        if ultimo_contenido_user:
            with lock:
                continuar = True
                return peticion_rag(ultimo_contenido_user, fecha, historial)
        else:
            with lock:
                continuar = False
                return "", 204  # Retornar un estado 204 (No Content)

    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})


def peticion_rag(texto_consulta, fecha, historial):
    """
    Realiza una búsqueda de similitud en una base de datos de Chroma, formatea un prompt basado en los 
    resultados de búsqueda y en los datos históricos, y genera una respuesta utilizando un modelo de Ollama.
    
    :param texto_consulta: Representa el texto de la consulta que se utiliza para buscar elementos similares en 
                           la base de datos. Es el texto de entrada que se utiliza como punto de referencia para la operación de búsqueda.
    :param fecha: Representa una fecha que se utiliza como filtro en la operación de búsqueda de similitud dentro 
                  de la base de datos de Chroma. Esta fecha se utiliza para reducir los resultados de búsqueda 
                  y solo incluir datos que coincidan con la fecha especificada.
    :param historial: Representa un registro o historial de interacciones o consultas anteriores. Se utiliza en la función para ayudar 
                      a generar un prompt para el modelo de lenguaje basado en el texto de consulta actual, las interacciones históricas y 
                      los resultados de búsqueda.
    :return Response: Objeto de respuesta con el contenido generado por la función `generate_ndjson`. El contenido está en formato NDJSON 
                      (JSON delimitado por saltos de línea) y el objeto de respuesta tiene el tipo MIME "application/x-ndjson". Si ocurre un 
                      error durante el proceso, se devuelve una respuesta JSON con el mensaje de error.
    """
    try:
        global load_duration
        db = Chroma(persist_directory=os.getenv("CHROMA_PATH"), embedding_function=get_funcion_embebido(),) # Inicializar la base de datos de Chroma
        resultados = db.similarity_search_with_score(texto_consulta, k=7, filter={"date": fecha}) # Realizar una búsqueda de similitud en la base de datos

        start_time_load = time.time()
        modelo = Ollama(model=os.getenv("MODEL_LLM"), num_ctx=int(os.getenv("MAX_TOKENS")),)
        load_duration = (time.time() - start_time_load) * 1000000
        
    except Exception as e:
        print(f"Error en hacer petición al LLM: {str(e)}")
        return jsonify({"error": f"Error en hacer petición al LLM: {str(e)}"})

    while True:
        prompt = formatear_prompt(resultados, texto_consulta, "\n".join(historial)) # Formatear el prompt con el historial actual y los resultados
        if modelo.get_num_tokens(prompt) <= int(os.getenv("MAX_TOKENS")): # Verificar el tamaño del prompt después de formatear
            break  # Salir del bucle si el tamaño del prompt está dentro del límite
        if historial: # Reducir el historial hasta que el tamaño del prompt esté dentro del límite
            historial.popleft() # Eliminar el primer elemento del historial
        else: # Si el historial está vacío, romper el bucle para evitar un bucle infinito
            break

    try:
        return Response(generate_ndjson(modelo, prompt, resultados), mimetype="application/x-ndjson")

    except Exception as e:
        print(f"Error en hacer petición al LLM: {str(e)}")
        return jsonify({"error": f"Error en hacer petición al LLM: {str(e)}"})

def generate_ndjson(modelo, prompt, resultados):
    """
    Transmite datos en formato NDJSON con métricas de tiempo incluidas.
    
    :param modelo: Utilizado para generar fragmentos de datos cuando se llama a `modelo.stream(prompt)`. 
                   Este generador se utiliza para procesar y transmitir datos para su posterior evaluación y procesamiento.
    :param prompt: Utilizado para generar fragmentos de datos a partir de un modelo dado y transmitir la salida en formato NDJSON. 
                   Cada fragmento de datos se procesa y se devuelve como un objeto JSON.
    :param resultados: Una lista de tuplas que contienen documentos y sus puntuaciones. La función procesa estos documentos para 
                       extraer metadatos como el ID del documento y genera una respuesta formateada en función de estos metadatos.
    :return Response: El contenido está en formato NDJSON (JSON delimitado por saltos de línea) y el objeto de respuesta tiene el tipo MIME "application/x-ndjson". 
                      Si ocurre un error durante el proceso, se devuelve una respuesta JSON con el mensaje de error.
    """
    
    start_time_total = time.time()
    prompt_eval_count = 0
    prompt_eval_duration = 0
    eval_count = 0
    eval_duration = 0
    for chunk in modelo.stream(prompt):
        start_time_prompt_eval = time.time() # Mide el tiempo de evaluación del prompt

        with lock:
            if continuar:
                created_at = datetime.now().isoformat() + "Z"
                yield json.dumps(
                    {
                        "created_at": created_at,
                        "message": {"role": "assistant", "content": chunk},
                        "done": False,
                    }
                ) + "\n"
            else:
                break

    if resultados:
        # Obtener el origen de los documentos
        fuentes = [
            doc.metadata.get("id", None)
            for doc, _score in sorted(
                resultados, key=lambda x: x[0].metadata.get("id", "").lower()
            )
        ]

        # Concatenar los orígenes de los documentos en una cadena
        respuesta_formateada = f"\n\n***Fuentes utilizadas:***\n"
        respuesta_formateada += "\n".join(
            [
                f"- **Archivo:** {source.split(':')[0]} | **Número de página:** {int(source.split(':')[1]) + 1} - **Fragmento:** {int(source.split(':')[2]) + 1}"
                for source in fuentes
            ]
        )
        yield json.dumps(
            {
                "created_at": created_at,
                "message": {"role": "assistant", "content": respuesta_formateada},
                "done": False,
            }
        ) + "\n"

        # Incrementa el contador de evaluaciones del prompt
        prompt_eval_count += 1

        # Incrementa el tiempo total de evaluación del prompt
        prompt_eval_duration += (
            time.time() - start_time_prompt_eval
        ) * 1000000  # En microsegundos

        # Mide el tiempo de evaluación general
        start_time_eval = time.time()

        # Añadir cualquier otra operación que se quiera medir en eval_duration
        # eval_duration += (time.time() - start_time_eval) * 1000000
        # eval_count += 1
        eval_duration += (time.time() - start_time_eval) * 1000000  # En microsegundos

    # Genera el NDJSON final con las métricas
    yield json.dumps(
        {
            "created_at": datetime.now().isoformat() + "Z",
            "message": {"role": "assistant", "content": ""},
            "done_reason": "stop",
            "done": True,
            "total_duration": (time.time() - start_time_total) * 1000000,
            "load_duration": load_duration,
            "prompt_eval_count": prompt_eval_count,
            "prompt_eval_duration": prompt_eval_duration,
            "eval_count": eval_count,
            "eval_duration": eval_duration,
        }
    ) + "\n"
