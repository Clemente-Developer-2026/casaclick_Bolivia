from flask import Flask
from flask_migrate import Migrate
from app.extensions import db, bcrypt, login_manager
from app.models import Usuario
from datetime import datetime

migrate = Migrate()
def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    db.init_app(app)
    bcrypt.init_app(app) 
    login_manager.init_app(app)
    migrate.init_app(app,db)

    @app.context_processor
    def inject_datetime():
        """Inyecta datetime en todos los templates"""
        return {'datetime': datetime}

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    


    # En app/app.py, después de crear la app
    from app.utils.uploads import get_image_url

    # Agregar un contexto para las imágenes
    @app.context_processor
    def inject_image_helpers():
        return {
            'get_image_url': get_image_url
        }
    
    #Importacion de los Blueprint 
    from app.main import main_bp
    from app.auth import auth_bp
    from app.cliente import cliente_bp
    from app.admin import admin_bp
    from app.vendedor import vendedor_bp

    #Registro de los Blueprint
    app.register_blueprint(auth_bp,url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(cliente_bp, url_prefix='/cliente')
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendedor_bp,url_prefix="/vendedor")



    with app.app_context():
        db.create_all()

    return app