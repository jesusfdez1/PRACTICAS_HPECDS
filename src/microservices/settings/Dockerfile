# Usa una imagen base oficial de Python
FROM python:3.12-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de requerimientos
COPY ./requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de la aplicación
COPY . .

# Expone el puerto en el que tu aplicación correrá
EXPOSE 5005

# Define el comando para ejecutar la aplicación
CMD ["python", "settings.py"]
