import os
import secrets
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    app = Flask(__name__)

    # ── Carrega configuração do config.py ───────────────────────────────────
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "production")

    from config import config as config_map
    app.config.from_object(config_map.get(config_name, config_map["default"]))

    # ── Extensões ───────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    # ── Nonce CSP por requisição ────────────────────────────────────────────
    @app.before_request
    def _generate_csp_nonce():
        """Gera um nonce criptograficamente seguro para cada requisição."""
        g.csp_nonce = secrets.token_urlsafe(16)

    # Torna o nonce disponível globalmente nos templates Jinja2
    @app.context_processor
    def _inject_csp_nonce():
        return {"csp_nonce": g.get("csp_nonce", "")}

    # ── Cabeçalhos de segurança ─────────────────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        nonce = g.get("csp_nonce", "")

        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"

        # CSP sem unsafe-inline no script — scripts permitidos apenas com o nonce correto
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' cdn.jsdelivr.net; "
            "style-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
            "font-src 'self' cdn.jsdelivr.net; "
            "img-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "object-src 'none';"
        )
        return response

    # ── Blueprints ──────────────────────────────────────────────────────────
    with app.app_context():
        from .blueprints.auth import auth_bp
        from .blueprints.junior import junior_bp
        from .blueprints.lider import lider_bp
        from .blueprints.supervisor import supervisor_bp
        from .blueprints.period import period_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(junior_bp, url_prefix="/junior")
        app.register_blueprint(lider_bp, url_prefix="/lider")
        app.register_blueprint(supervisor_bp, url_prefix="/supervisor")
        app.register_blueprint(period_bp, url_prefix="/periodo")

    return app