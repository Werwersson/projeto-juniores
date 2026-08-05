import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-super-secreta')
    
    db.init_app(app)
    login_manager.init_app(app)
    
    # --- ADICIONE ESTAS DUAS LINHAS ---
    # Substitua 'auth.login' pelo nome do seu blueprint e função de login
    login_manager.login_view = 'auth.login' 
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    # ----------------------------------

    from app.blueprints.period import period_bp
    app.register_blueprint(period_bp)
    
    return app
