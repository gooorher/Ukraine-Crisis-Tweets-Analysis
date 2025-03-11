from flask import Blueprint, render_template, jsonify, request, current_app
import logging

bp = Blueprint('geo', __name__, url_prefix='/geo')
logger = logging.getLogger(__name__)

@bp.route('/')
def geo_page():
    """Página principal de análisis geográfico"""
    try:
        return render_template('geo/geo.html')
    except Exception as e:
        logger.error(f"Error al cargar la página de análisis geográfico: {str(e)}")
        return render_template('errors/500.html'), 500