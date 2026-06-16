from flask import Blueprint

vendedor_bp = Blueprint("vendedor",__name__,url_prefix="/vendedor")

from app.vendedor import routes