from flask import Flask
from flask_migrate import Migrate
from app.extensions import db, bcrypt, login_manager
from app.models import Usuario

migrate = Migrate()
def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")
    db.init_app(app)
    bcrypt.init_app(app) 
    login_manager.init_app(app)
    migrate.init_app(app,db)



    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    #Importacion de los Blueprint 
    from app.main import main_bp
    from app.auth import auth_bp
    from app.cliente import cliente_bp

    #Registro de los Blueprint
    app.register_blueprint(auth_bp,url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(cliente_bp, url_prefix='/cliente')



    with app.app_context():
        db.create_all()

    return app