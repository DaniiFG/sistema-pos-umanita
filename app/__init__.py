from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # A dónde ir si no está logueado
login_manager.login_message = "Debes iniciar sesión para ver esto."
login_manager.login_message_category = "warning"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Cargar usuario para Flask-Login
    from app.models import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Blueprints
    from app.modules.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.modules.ventas.routes import ventas_bp
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    
    from app.modules.gastos.routes import gastos_bp
    app.register_blueprint(gastos_bp, url_prefix='/gastos')
    
    from app.modules.inventario.routes import inventario_bp
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    
    from app.modules.informes.routes import informes_bp
    app.register_blueprint(informes_bp, url_prefix='/informes')
    
    from app.modules.productos.routes import productos_bp
    app.register_blueprint(productos_bp, url_prefix='/productos')
    
    return app