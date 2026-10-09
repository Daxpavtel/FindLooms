from flask import Blueprint

kanban_bp = Blueprint("kanban", __name__, url_prefix="/kanban")

from . import routes  # noqa
