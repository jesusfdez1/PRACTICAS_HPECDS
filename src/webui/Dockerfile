# Etapa 1: Construcción
FROM node:18-alpine AS build

WORKDIR /app

# Copia los archivos de configuración de npm
COPY package*.json ./

# Instala las dependencias
RUN npm install

# Copia el resto del código fuente de la aplicación
COPY . .

# Construye la aplicación Svelte con Vite
RUN npm run build

# Comando de depuración para verificar que el build se generó correctamente
RUN ls -l /app/dist

# Etapa 2: Servir la aplicación
FROM nginx:alpine

# Copia los archivos construidos desde la etapa anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Exponer el puerto 80 para que Nginx pueda servir la aplicación
EXPOSE 80

# Comando para correr Nginx
CMD ["nginx", "-g", "daemon off;"]
