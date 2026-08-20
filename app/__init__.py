import os
from urllib import response
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name="production"):
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-super-secreta')

    db_url = os.environ.get('DATABASE_URL') or 'sqlite:///banco_local.db'
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' cdn.jsdelivr.net fonts.googleapis.com 'unsafe-inline'; "
            "font-src 'self' cdn.jsdelivr.net fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        return response

    with app.app_context():
        from .blueprints.auth import auth_bp
        from .blueprints.junior import junior_bp
        from .blueprints.lider import lider_bp
        from .blueprints.supervisor import supervisor_bp
        from .blueprints.period import period_bp
        
        app.register_blueprint(auth_bp)
        app.register_blueprint(junior_bp, url_prefix='/junior')
        app.register_blueprint(lider_bp, url_prefix='/lider')
        app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
        app.register_blueprint(period_bp, url_prefix='/periodo')
        
    return app