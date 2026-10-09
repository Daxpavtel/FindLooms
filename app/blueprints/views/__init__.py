from flask import Blueprint

views_bp = Blueprint("views", __name__, url_prefix="/views")

from . import routes  # noqa
