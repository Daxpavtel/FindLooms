from flask import Blueprint

found_bp = Blueprint("found", __name__, url_prefix="/found")

from . import routes  # noqa
