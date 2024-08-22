#!/bin/sh

# Iniciar Ollama en segundo plano
/bin/ollama serve &

sleep 10

# Descargar los modelos requeridos
/bin/ollama pull joanfm/jina-embeddings-v2-base-es || { echo "Fallo al descargar joanfm/jina-embeddings-v2-base-es"; exit 1; }
/bin/ollama pull llama3.1:8b-instruct-q5_K_M || { echo "Fallo al descargar llama3.1:8b-instruct-q5_K_M"; exit 1; }

# Mantener el contenedor en ejecución
wait
