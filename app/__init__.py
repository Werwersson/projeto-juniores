from flask import Flask
from app.extensions import db  # Importando do novo arquivo neutro

def create_app():
    app = Flask(__name__)
    
    # Suas configurações de banco de dados e chaves secretas...
    
    db.init_app(app)

    # O registro dos seus blueprints deve acontecer AQUI
    from app.blueprints.period import period_bp
    app.register_blueprint(period_bp)
    
    return app
