from flask import Blueprint

bp = Blueprint('language', __name__, url_prefix='/language')

@bp.route('/')
def language():
    return "Language Route"