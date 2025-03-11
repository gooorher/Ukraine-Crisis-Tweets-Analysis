from flask import Blueprint, render_template, jsonify, request, current_app
from datetime import datetime, timedelta
import logging
from flask_app.services import trends_service
from flask_app.utils.date_utils import parse_date_range
import traceback

bp = Blueprint('trends', __name__, url_prefix='/trends')
logger = logging.getLogger(__name__)

@bp.route('/')
def trends_page():
    """Página principal de tendencias"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Obteniendo tendencias para el rango: {date_range['start_date']} - {date_range['end_date']}")
        return render_template('trends.html')
    except Exception as e:
        logger.error(f"Error al cargar la página de tendencias: {str(e)}\n{traceback.format_exc()}")
        return render_template('errors/500.html'), 500

@bp.route('/api/data')
def get_trends_data():
    """API endpoint para obtener datos de tendencias"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Obteniendo datos de tendencias para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        trends_data = trends_service.get_trends(date_range)
        logger.debug(f"Datos obtenidos: {trends_data}")
        
        return jsonify({
            'success': True,
            'data': trends_data
        })
    except Exception as e:
        logger.error(f"Error al obtener datos de tendencias: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/volume')
def get_volume_data():
    """API endpoint para obtener datos de volumen de tweets"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Obteniendo datos de volumen para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        volume_data = trends_service.get_tweet_volume(date_range)
        logger.debug(f"Datos obtenidos: {volume_data}")
        
        return jsonify({
            'success': True,
            'data': volume_data
        })
    except Exception as e:
        logger.error(f"Error al obtener datos de volumen: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/engagement')
def get_engagement_data():
    """API endpoint para obtener datos de engagement"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Obteniendo datos de engagement para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        engagement_data = trends_service.get_engagement_metrics(date_range)
        logger.debug(f"Datos obtenidos: {engagement_data}")
        
        return jsonify({
            'success': True,
            'data': engagement_data
        })
    except Exception as e:
        logger.error(f"Error al obtener datos de engagement: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/hourly')
def get_hourly_data():
    """API endpoint para obtener distribución horaria"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Obteniendo distribución horaria para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        hourly_data = trends_service.get_hourly_distribution(date_range)
        logger.debug(f"Datos obtenidos: {hourly_data}")
        
        return jsonify({
            'success': True,
            'data': hourly_data
        })
    except Exception as e:
        logger.error(f"Error al obtener distribución horaria: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/export/<format>')
def export_data(format):
    """Exportar datos en formato CSV o JSON"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Exportando datos en formato {format} para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        if format not in ['csv', 'json']:
            return jsonify({
                'success': False,
                'error': 'Formato no soportado'
            }), 400
            
        trends_data = trends_service.get_trends(date_range)
        
        if format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Escribir encabezados
            writer.writerow(['date', 'tweet_count', 'total_engagement', 'unique_users', 'avg_engagement'])
            
            # Escribir datos
            for row in trends_data:
                writer.writerow([
                    row['date'],
                    row['tweet_count'],
                    row['total_engagement'],
                    row['unique_users'],
                    row['avg_engagement']
                ])
            
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=trends_{date_range["start_date"].strftime("%Y-%m-%d %H_%M_%S")}_{date_range["end_date"].strftime("%Y-%m-%d %H_%M_%S")}.csv'
            }
        else:  # JSON
            return jsonify(trends_data), 200, {
                'Content-Disposition': f'attachment; filename=trends_{date_range["start_date"].strftime("%Y-%m-%d %H_%M_%S")}_{date_range["end_date"].strftime("%Y-%m-%d %H_%M_%S")}.json'
            }
            
    except Exception as e:
        logger.error(f"Error al exportar datos: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500