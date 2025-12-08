# config.py
import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'umanita.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'pollo-broaster-seguro'
    
    # Configuración de subida de imágenes
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max