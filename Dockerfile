FROM python:3.12.4
FROM node:14

COPY . /

WORKDIR /

# Every needed package is installed from requirements.txt
RUN pip install -r requirements.txt
RUN npm install /src/webui/package.json

# We need to set the host to 0.0.0.0 to allow outside access
ENV HOST 0.0.0.0

CMD [ "python" , "./src/server.py" ]

# Copy needed files
COPY ./model/model.gguf /app/model.gguf
COPY ./code/server.py /app/server.py

# Port to expose to run the server
EXPOSE 8501

# Web server script is run when the container is started
ENTRYPOINT ["streamlit", "run", "server.py", "--server.port=8501", "--server.address=0.0.0.0"]