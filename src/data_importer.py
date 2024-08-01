from flask import request
import os
import fitz
import datetime
from constants import PATH_PDFS
import re

def import_data():
    files = request.files.getlist("files[]")
    # Si no existe la carpeta pdfs, se crea
    try:
        os.makedirs(PATH_PDFS, exist_ok=True)
    except OSError:
        print("No se pudo acceder al directorio para guardar los archivos.")
        return "Internal Server Error", 500
        
    for file in files:
        try:
            file.save(f'{PATH_PDFS}/{file.filename}')
        except Exception as e:
            print(f"Error al guardar archivo: {e}")
            return "Internal Server Error", 500

    return "OK", 200

def data_dates():
    dates = set()
    # Si no existe la carpeta pdfs, error
    if not os.path.exists(PATH_PDFS):
        return dates
    
    for file in os.listdir(PATH_PDFS):
        file_path = os.path.join(PATH_PDFS, file)
        if os.path.isfile(file_path) and file.lower().endswith('.pdf'):
            try:
                # Abrir el archivo PDF y leer sus metadatos
                pdf_document = fitz.open(file_path)
                metadata = pdf_document.metadata
                pdf_document.close()
                
                # Obtener el campo "Palabras clave"
                keywords = metadata.get("keywords", "")
                # Obtener el último valor separado por ;
                if keywords:
                    last_value = keywords.split(";")[-1].strip()
                    try:
                        # Intentar convertir el último valor en una fecha
                        last_date = datetime.datetime.strptime(last_value, "%d/%m/%Y")
                        dates.add(last_date)
                    except ValueError:
                            last_value = keywords.split(";")[3].strip()
                            dates.add(obtener_fecha_desde_texto(last_value))
            except Exception as e:
                print(f"Error al procesar archivo {file}: {e}")
                pass
    return sorted(list(dates))

def obtener_fecha_desde_texto(texto):
    patron_fecha = r'(?P<dia_semana>\w+)\s+(?P<dia>\d{1,2})\s+de\s+(?P<mes>\w+)\s+de\s+(?P<anio>\d{4})\s*'
    match_fecha = re.search(patron_fecha, texto, re.IGNORECASE)
    
    if match_fecha:
        dia = int(match_fecha.group('dia'))
        mes_str = match_fecha.group('mes').lower()
        anio = int(match_fecha.group('anio'))
        
        meses = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
        mes = meses.get(mes_str)
        
        if mes:
            return datetime.datetime(anio, mes, dia)

