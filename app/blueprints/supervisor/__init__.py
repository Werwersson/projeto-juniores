from flask import Blueprint

supervisor_bp = Blueprint("supervisor", __name__, template_folder="templates")

from app.blueprints.supervisor import routes  # noqa: E402, F401
