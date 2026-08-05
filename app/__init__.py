import os
from flask import Flask
from app.extensions import db

def create_app():
    app = Flask(__name__)
    
    # Adicione esta linha para puxar a URL do banco do ambiente
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    
    db.init_app(app)

    from app.blueprints.period import period_bp
    app.register_blueprint(period_bp)
    
    return app
