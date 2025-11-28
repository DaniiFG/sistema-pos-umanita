from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Inicializamos la extensión de BD
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Registro de Blueprints (Módulos)
    # Nota: Importamos aquí para evitar referencias circulares
    from app.modules.ventas.routes import ventas_bp
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    
    # Aquí registraremos inventario, gastos, etc. en el futuro
    from app.modules.gastos.routes import gastos_bp
    app.register_blueprint(gastos_bp, url_prefix='/gastos')
    
    from app.modules.inventario.routes import inventario_bp
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    
    from app.modules.informes.routes import informes_bp
    app.register_blueprint(informes_bp, url_prefix='/informes')
    
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen

    return app