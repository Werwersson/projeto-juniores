import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Instanciando o banco de dados e o gerenciador de login
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name="production"):
    app = Flask(__name__)
    
    # 1. Configura a chave secreta
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-super-secreta')
    
    # 2. Configura a URL do banco de dados do Vercel
    db_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL') or 'sqlite:///banco_local.db'
    
    # Corrige a URL do Postgres se necessário (exigência do SQLAlchemy atual)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 3. Inicializa as extensões com o App
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurações do Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    with app.app_context():
        # Importando os blueprints
        from .blueprints.auth import auth_bp
        from .blueprints.junior import junior_bp
        from .blueprints.lider import lider_bp
        from .blueprints.supervisor import supervisor_bp
        from .blueprints.period import period_bp
        
        # Registrando no app
        app.register_blueprint(auth_bp)
        app.register_blueprint(junior_bp)
        app.register_blueprint(lider_bp)
        app.register_blueprint(supervisor_bp)
        app.register_blueprint(period_bp)
        
    return app