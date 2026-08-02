from flask import Blueprint

junior_bp = Blueprint("junior", __name__, template_folder="templates")

from app.blueprints.junior import routes  # noqa: E402, F401
