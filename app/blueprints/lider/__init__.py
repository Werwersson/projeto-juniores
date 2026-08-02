from flask import Blueprint

lider_bp = Blueprint("lider", __name__, template_folder="templates")

from app.blueprints.lider import routes  # noqa: E402, F401
