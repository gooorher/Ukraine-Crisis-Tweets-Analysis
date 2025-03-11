from flask import Blueprint, render_template, jsonify, request, current_app
from flask_app.services import hashtags_service
from flask_app.utils.date_utils import parse_date_range
import logging
import traceback

bp = Blueprint('hashtags', __name__, url_prefix='/hashtags')
logger = logging.getLogger(__name__)

@bp.route('/')
def hashtags_page():
    """Página principal de visualización de hashtags"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Cargando página de hashtags para el rango: {date_range['start_date']} - {date_range['end_date']}")
        return render_template('hashtags.html')
    except Exception as e:
        logger.error(f"Error al cargar la página de hashtags: {str(e)}\n{traceback.format_exc()}")
        return render_template('errors/500.html'), 500

@bp.route('/api/frequency')
def get_hashtag_frequency():
    """API endpoint para obtener la frecuencia de hashtags"""
    try:
        date_range = parse_date_range(request.args)
        limit = request.args.get('limit', default=20, type=int)
        
        logger.info(f"Obteniendo frecuencia de hashtags para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        frequency_data = hashtags_service.get_hashtag_frequency(date_range, limit=limit)
        logger.debug(f"Datos obtenidos: {len(frequency_data)} hashtags")
        
        return jsonify({
            'success': True,
            'data': frequency_data
        })
    except Exception as e:
        logger.error(f"Error al obtener frecuencia de hashtags: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/popularity')
def get_hashtag_popularity():
    """API endpoint para obtener la evolución temporal de hashtags"""
    try:
        date_range = parse_date_range(request.args)
        
        # Obtener y validar hashtags
        hashtags = request.args.getlist('hashtags[]')
        if hashtags:
            hashtags = [h.strip() for h in hashtags if h.strip()]
            logger.info(f"Hashtags solicitados: {hashtags}")
        
        limit = request.args.get('limit', default=5, type=int)
        
        logger.info(f"Obteniendo evolución de hashtags para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        popularity_data = hashtags_service.get_hashtag_popularity_over_time(
            date_range,
            top_hashtags=hashtags if hashtags else None,
            limit=limit
        )
        
        logger.debug(f"Datos obtenidos para {len(popularity_data)} hashtags")
        for hashtag, data in popularity_data.items():
            logger.debug(f"Hashtag {hashtag}: {len(data)} puntos de datos")
        
        return jsonify({
            'success': True,
            'data': popularity_data
        })
    except Exception as e:
        logger.error(f"Error al obtener evolución de hashtags: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/cooccurrence')
def get_hashtag_cooccurrence():
    """API endpoint para obtener la red de co-ocurrencia de hashtags"""
    try:
        date_range = parse_date_range(request.args)
        min_occurrences = request.args.get('min_occurrences', default=10, type=int)
        
        logger.info(f"Obteniendo red de co-ocurrencia para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        network_data = hashtags_service.get_hashtag_cooccurrence(
            date_range,
            min_occurrences=min_occurrences
        )
        
        logger.debug(f"Datos obtenidos: {len(network_data['nodes'])} nodos y {len(network_data['links'])} enlaces")
        
        return jsonify({
            'success': True,
            'data': network_data
        })
    except Exception as e:
        logger.error(f"Error al obtener red de co-ocurrencia: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/export')
def export_hashtag_data():
    """API endpoint para exportar datos de hashtags"""
    try:
        date_range = parse_date_range(request.args)
        format = request.args.get('format', default='json')
        
        logger.info(f"Exportando datos de hashtags en formato {format} para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        # Obtener datos
        frequency_data = hashtags_service.get_hashtag_frequency(date_range, limit=100)
        top_hashtags = [h['hashtag'] for h in frequency_data[:10]]
        popularity_data = hashtags_service.get_hashtag_popularity_over_time(date_range, top_hashtags=top_hashtags)
        cooccurrence_data = hashtags_service.get_hashtag_cooccurrence(date_range)
        
        export_data = {
            'date_range': {
                'start': date_range['start_date'].isoformat(),
                'end': date_range['end_date'].isoformat()
            },
            'frequency': frequency_data,
            'popularity': popularity_data,
            'cooccurrence': cooccurrence_data
        }
        
        if format == 'csv':
            # TODO: Implementar exportación CSV
            return jsonify({
                'success': False,
                'error': 'Formato CSV no implementado'
            }), 501
        
        return jsonify({
            'success': True,
            'data': export_data
        })
    except Exception as e:
        logger.error(f"Error al exportar datos de hashtags: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
