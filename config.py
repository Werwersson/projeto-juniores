import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Segurança ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY não definida no .env. "
            "Gere uma com: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # ── Banco ──────────────────────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _db_url = os.environ.get("DATABASE_URL", "")
    if not _db_url:
        raise RuntimeError("DATABASE_URL não definida no .env.")
    SQLALCHEMY_DATABASE_URI = _db_url.replace("postgres://", "postgresql://", 1)

    # ── Cookies de sessão seguros ──────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True   # Inacessível via JavaScript
    SESSION_COOKIE_SAMESITE  = "Lax" # Bloqueia CSRF cross-site
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"  # Bloqueia CSRF via cookie remember-me
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30  # 30 dias

    # ── Rate limiting ──────────────────────────────────────────────────────────
    LOGIN_MAX_ATTEMPTS  = 5    # Tentativas antes de bloquear
    LOGIN_BLOCK_SECONDS = 300  # 5 minutos de bloqueio


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # HTTP local


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True   # Só HTTPS
    REMEMBER_COOKIE_SECURE = True


# Usa ProductionConfig por padrão — força explicitação de ambiente de dev
_env = os.environ.get("FLASK_ENV", "production")
config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     ProductionConfig,
}
