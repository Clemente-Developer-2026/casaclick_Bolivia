# app/utils/uploads.py
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg', 'ico'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    """
    Guardar una imagen en el directorio de uploads
    Retorna el nombre del archivo guardado
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Generar nombre único
    extension = file.filename.rsplit('.', 1)[1].lower()
    nombre_archivo = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{extension}"
    
    # Crear directorio si no existe
    upload_folder = os.path.join(current_app.root_path, 'utils', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Guardar archivo
    file_path = os.path.join(upload_folder, nombre_archivo)
    file.save(file_path)
    
    return nombre_archivo

def delete_image(filename):
    """Eliminar una imagen del sistema de archivos"""
    if not filename:
        return False
    
    upload_folder = os.path.join(current_app.root_path, 'utils', 'uploads')
    file_path = os.path.join(upload_folder, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def get_image_url(filename):
    """Obtener la URL de una imagen"""
    if not filename:
        return None
    return f"/utils/uploads/{filename}"