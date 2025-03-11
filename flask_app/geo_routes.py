from flask import Blueprint

bp = Blueprint('geo', __name__, url_prefix='/geo')

@bp.route('/')
def geo():
    return "Geo Route"