from flask import Blueprint, render_template, jsonify, request, current_app
import logging

bp = Blueprint('language', __name__, url_prefix='/language')
logger = logging.getLogger(__name__)

@bp.route('/')
def language_page():
    """Página principal de análisis de idiomas"""
    try:
        return render_template('language/language.html')
    except Exception as e:
        logger.error(f"Error al cargar la página de análisis de idiomas: {str(e)}")
        return render_template('errors/500.html'), 500