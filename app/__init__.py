import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    # Configurações de ambiente
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-super-secreta')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Trata URLs de banco que começam com "postgres://" para o SQLAlchemy 2.x
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
            "postgres://", "postgresql://", 1
        )
    
    # Inicialização das extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurações do Flask-Login
    login_manager.login_view = 'auth.login' 
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'

    # User loader para o Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- REGISTRO DE TODOS OS BLUEPRINTS ---
    from app.blueprints.auth import auth_bp
    from app.blueprints.supervisor import supervisor_bp
    from app.blueprints.lider import lider_bp
    from app.blueprints.junior import junior_bp
    from app.blueprints.period import period_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(supervisor_bp)
    app.register_blueprint(lider_bp)
    app.register_blueprint(junior_bp)
    app.register_blueprint(period_bp)
    # --------------------------------------
    
    return app