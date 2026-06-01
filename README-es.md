# Sistema de Consulta y Gestión de Documentos del BOE mediante LLM

[Español](README-es.md) | [English](README.md)

Este proyecto está diseñado para permitir a los usuarios interactuar con el *Boletín Oficial del Estado* (BOE) facilitando la consulta, procesamiento y gestión de documentos basados en fechas de publicación específicas.

El sistema utiliza Grandes Modelos de Lenguaje (LLMs) para procesar los documentos del BOE y realizar análisis léxico y semántico. Además, implementa una arquitectura de búsqueda basada en *embeddings* para identificar y extraer contexto relevante con alta precisión. Esto permite a los usuarios ejecutar búsquedas semánticas y recuperar resultados eficientemente. El objetivo final es proporcionar una herramienta robusta y accesible para la obtención y gestión de información del BOE.

![Interfaz general de la aplicación](readme/1.png)

## Índice
- [1. Características principales](#1-características-principales)
- [2. Arquitectura del proyecto](#2-arquitectura-del-proyecto)
- [3. Uso de Nginx como Proxy en Docker Compose](#3-uso-de-nginx-como-proxy-en-docker-compose)
- [4. Dependencias y frameworks](#4-dependencias-y-frameworks)
- [5. Interfaz web](#5-interfaz-web)

## 1. Características principales
El sistema incluye un conjunto de funcionalidades diseñadas para la gestión estructurada de documentos del BOE:

- **Descarga del BOE por fecha**: Permite buscar y descargar entradas del BOE especificando días concretos o rangos de fechas, asegurando una recuperación ágil de datos.
- **Importación de documentos locales**: Proporciona a los usuarios la capacidad de indexar archivos locales para su procesamiento, flexibilizando el uso de la herramienta para conjuntos de documentos externos.

<p align="center">
  <img src="readme/3.png" alt="Descarga del BOE" width="450"/>
  <img src="readme/4.png" alt="Importación de documentos" width="450"/>
</p>

- **Configuración de parámetros**: Mediante una interfaz web intuitiva, el usuario puede ajustar directrices de procesamiento de texto, tales como `CHUNK_SIZE` y `CHUNK_OVERLAP`, permitiendo optimizar el particionado de datos según los recursos de hardware disponibles.
- **Interfaz gráfica adaptable**: Incluye soporte nativo para los modos oscuro y claro, posibilitando a cada usuario adaptar visualmente la interfaz de trabajo.
- **Eliminación segura de datos**: Permite la purga completa y segura de la base de datos vectorial y los documentos almacenados mediante un comando directo, asegurando el cumplimiento de normativas de retención de datos.

<p align="center">
    <img src="readme/2.png" alt="Otras configuraciones" width="500"/>
</p>

- **Consultas avanzadas en documentos históricos**: Facilita la extracción de contenido y ejecución de consultas semánticas focalizadas en los conjuntos de datos previamente descargados.
- **Gestión integral de conversaciones**:
    - **Generación automática de títulos**: Clasificación e indexación automática de los hilos de conversación mediante síntesis LLM.
    - **Limpieza de historial**: Elimina definitivamente la retención de los registros de chat interconectados a las sesiones.
    - **Importación/Exportación**: Integración fluida mediante la ingesta o volcado de los historiales en formato estructurado JSON.
- **Monitorización de errores y telemetría**: Notificación directa de estados de ejecución y errores sistémicos para asegurar un conocimiento íntegro de la salud del de servicio.

## 2. Arquitectura del proyecto
Dada la naturaleza evolutiva del proyecto, este se encuentra estructurado en tres estrategias de despliegue aisladas mediante ramas de GitHub:

- **`main`**: Emplea una arquitectura estándar de cliente-servidor sin contenedorización Docker. Un servidor centralizado en Python gestiona de manera unificada las peticiones.
- **`docker-clientserver`**: Contenedoriza la arquitectura base servidor-cliente mediante Docker para entornos normalizados.
- **`docker-microservices`**: Implementa una arquitectura en malla de microservicios con Docker Compose, maximizando la resiliencia y escalabilidad independiente de los contenedores.

## 3. Uso de Nginx como Proxy en Docker Compose
Este repositorio aprovecha las capacidades de Docker Compose para la orquestación del mapa de microservicios, desplegando un servicio Nginx como proxy inverso principal.

### Configuración Nginx
Nginx se compila de forma aislada e independiente en el `docker-compose.yml`. Las normativas de enrutamiento dinámico están descritas en `nginx.conf`, conectando el puerto *host* `3001` hacia el puerto `80` del contenedor Nginx. La redirección del enrutador procede de la siguiente manera:

- Aquellas peticiones hacia `localhost:3001/chat` se delegarán al microservicio de inferencia en el puerto `5001`.
- Las peticiones a `localhost:3001/dates` derivarán al respectivo procesador de calendario y descargas en el puerto `5007`.

Ambos microservicios comparten acceso a la red lógica puente `app-network` de Docker interconectando sus operaciones eficientemente de manera interna sin exposición directa de los puertos subyacentes.

## 4. Dependencias y frameworks
El desarrollo de esta plataforma descansa sobre una selección meticulosa de tecnologías:

### Entornos de Ejecución
- **Ollama**: Infraestructura empleada para la carga local y orquestación temporal de modelos LLM requeridos para las analíticas avanzadas.
- **Node.js 18**: Entorno base de ejecución de la lógica Front-End, proporcionando alta concurrencia operacional I/O mediante su asincronía originaria.

### Modelos Cognitivos y Procesamiento Vectorial
- **Llama 3.1 (8B Instruct q5_K_M)**: Motor de generación primaria para síntesis y extracción del contexto semántico oficial del Boletín Oficial del Estado. Su ponderación rinde un excelente equilibrio computacional frente a hardware comercial.
- **joanfm/jina-embeddings-v2-base-es**: Modelo avanzado de recálculo vectorial (embeddings) entrenado orgánicamente sobre sintaxis en idioma español, aportando un salto representativo en la fidelidad de búsquedas en BOE.

### Dependencias Secundarias y Python
La instanciación en crudo requiere la instalación pre-requisito de las dependencias descritas explícitamente en el archivo `requirements.txt` bajo entornos estandarizados de `pip`.

## 5. Interfaz web
La instancia de cliente web ha sido reconstruida de base a partir de *Ollama Web UI Lite*, transformando su estructura original para abordar concretamente los alcances técnicos de la herramienta orientada al análisis BOE:

- **Refactorización bajo TypeScript**: Exige tipado férreo garantizando la escalabilidad lógica, detección estática de conflictos y facilidad procedimental de trabajo.
- **Modularidad arquitectónica**: Fracciona los componentes web facilitando reajustes limpios sobre el enrutamiento gráfico u operacional.
- **Pruebas de verificación**: Cobertura estricta para garantizar un alto grado de fiabilidad, aislando módulos y anticipando su estabilidad comportamental sobre el árbol web principal.