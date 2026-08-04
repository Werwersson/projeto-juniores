from flask import Blueprint

periodo_bp = Blueprint("periodo", __name__, template_folder="templates")

from app.blueprints.periodo import routes  # noqa: E402, F401
