import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Adicionamos o 'config_name' aqui para bater com o seu run.py
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
    
    # 3. Inicializa o SQLAlchemy com o App
    db.init_app(app)

    with app.app_context():
        with app.app_context():
            # Exemplo: importando os arquivos onde estão suas rotas
            from .routes import auth, junior, lider, supervisor
            
            # Registrando no app
            app.register_blueprint(auth.bp)
            app.register_blueprint(junior.bp)
            app.register_blueprint(lider.bp)
            app.register_blueprint(supervisor.bp)
        pass 
        
    return app