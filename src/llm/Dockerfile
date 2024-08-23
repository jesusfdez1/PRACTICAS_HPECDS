# Usar la imagen base de Ollama
FROM ollama/ollama:0.3.7-rc4

# Exponer el puerto por defecto de Ollama
EXPOSE 11434

# Copiar un script de inicio personalizado
COPY llm.sh /llm.sh

# Asegurarse de que el script tenga permisos de ejecución
RUN chmod +x /llm.sh

# Utilizar ENTRYPOINT para lanzar Ollama con el script personalizado
ENTRYPOINT ["/llm.sh"]
