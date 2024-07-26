import os
#Obtener el directorio del proyecto central
PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_MICROSERVICES_BASE_URL = 'localhost'
API_MICROSERVICES_PORT = 3001
PATH_PDFS = f'{PATH}/pdfs'