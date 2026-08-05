import os
from flask import Flask
from app.extensions import db, login_manager  # Importando os dois agora!

def create_app():
    app = Flask(__name__)
    
    # Configurações básicas (puxando do Vercel ou usando padrão local)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '')
    
    # Inicializando as extensões com o app
    db.init_app(app)
    login_manager.init_app(app)

    # Registro de Blueprints
    from app.blueprints.period import period_bp
    app.register_blueprint(period_bp)
    
    return app
