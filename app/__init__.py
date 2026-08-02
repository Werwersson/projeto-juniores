from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar esta página."
login_manager.login_message_category = "warning"


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    with app.app_context():
        from app.models import user, pgm, activity  # noqa: F401

    from app.blueprints.auth import auth_bp
    from app.blueprints.supervisor import supervisor_bp
    from app.blueprints.lider import lider_bp
    from app.blueprints.junior import junior_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(supervisor_bp, url_prefix="/supervisor")
    app.register_blueprint(lider_bp, url_prefix="/lider")
    app.register_blueprint(junior_bp, url_prefix="/junior")

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app