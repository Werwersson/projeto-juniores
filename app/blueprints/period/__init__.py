from flask import Blueprint

period_bp = Blueprint("period", __name__, template_folder="templates")

from app.blueprints.period import routes  # noqa: E402, F401
