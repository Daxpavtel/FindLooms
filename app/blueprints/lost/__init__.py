from flask import Blueprint

lost_bp = Blueprint("lost", __name__, url_prefix="/lost")

from . import routes  # noqa
