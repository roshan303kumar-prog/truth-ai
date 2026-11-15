from flask import Blueprint

views_bp = Blueprint("views", __name__)
auth_bp = Blueprint("auth", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

from . import view_routes, auth_routes, api_routes
