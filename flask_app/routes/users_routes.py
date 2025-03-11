from flask import Blueprint, render_template, jsonify, request, current_app
from flask_app.services import users_service
from flask_app.utils.date_utils import parse_date_range
import logging
import traceback

bp = Blueprint('users', __name__, url_prefix='/users')
logger = logging.getLogger(__name__)

@bp.route('/')
def users_page():
    """Página principal de visualización de usuarios"""
    try:
        date_range = parse_date_range(request.args)
        logger.info(f"Cargando página de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        return render_template('users.html')
    except Exception as e:
        logger.error(f"Error al cargar la página de usuarios: {str(e)}\n{traceback.format_exc()}")
        return render_template('errors/500.html'), 500

@bp.route('/api/activity')
def get_user_activity():
    """API endpoint para obtener la actividad de usuarios"""
    try:
        date_range = parse_date_range(request.args)
        limit = request.args.get('limit', default=20, type=int)
        
        logger.info(f"Obteniendo actividad de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        activity_data = users_service.get_user_activity(date_range, limit=limit)
        logger.debug(f"Datos obtenidos para {len(activity_data)} usuarios")
        
        return jsonify({
            'success': True,
            'data': activity_data
        })
    except Exception as e:
        logger.error(f"Error al obtener actividad de usuarios: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/engagement')
def get_user_engagement():
    """API endpoint para obtener métricas de engagement de usuarios"""
    try:
        date_range = parse_date_range(request.args)
        limit = request.args.get('limit', default=20, type=int)
        
        logger.info(f"Obteniendo engagement de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        engagement_data = users_service.get_user_engagement(date_range, limit=limit)
        logger.debug(f"Datos obtenidos para {len(engagement_data)} usuarios")
        
        return jsonify({
            'success': True,
            'data': engagement_data
        })
    except Exception as e:
        logger.error(f"Error al obtener engagement de usuarios: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/influence')
def get_user_influence():
    """API endpoint para obtener métricas de influencia de usuarios"""
    try:
        # Validar parámetros
        date_range = parse_date_range(request.args)
        limit = max(min(int(request.args.get('limit', 20)), 50), 5)  # Entre 5 y 50
        
        logger.info(
            f"Calculando influencia de usuarios:\n"
            f"- Rango: {date_range['start_date']} - {date_range['end_date']}\n"
            f"- Límite: {limit} usuarios"
        )
        
        # Obtener datos
        influence_data = users_service.get_user_influence(date_range, limit=limit)
        
        if not influence_data:
            logger.warning("No se encontraron datos de usuarios para el rango especificado")
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No se encontraron datos para el rango especificado'
            })
        
        # Validar resultados
        logger.info(
            f"Resultados de influencia:\n"
            f"- Usuarios procesados: {len(influence_data)}\n"
            f"- Rango de scores: {min(d['influence_score'] for d in influence_data):.2f} - "
            f"{max(d['influence_score'] for d in influence_data):.2f}"
        )
        
        return jsonify({
            'success': True,
            'data': influence_data,
            'metadata': {
                'total_users': len(influence_data),
                'date_range': {
                    'start': date_range['start_date'].isoformat(),
                    'end': date_range['end_date'].isoformat()
                }
            }
        })
    except Exception as e:
        logger.error(f"Error al obtener influencia de usuarios: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/user/<username>')
def get_user_details(username):
    """API endpoint para obtener detalles de un usuario específico"""
    try:
        date_range = parse_date_range(request.args)
        
        logger.info(f"Obteniendo detalles del usuario {username} para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        user_data = users_service.get_user_details(username, date_range)
        logger.debug(f"Datos obtenidos para el usuario {username}")
        
        return jsonify({
            'success': True,
            'data': user_data
        })
    except Exception as e:
        logger.error(f"Error al obtener detalles del usuario: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/evolution')
def get_user_evolution():
    """API endpoint para obtener la evolución temporal de métricas de usuarios"""
    try:
        date_range = parse_date_range(request.args)
        usernames = request.args.getlist('users[]')
        limit = request.args.get('limit', default=5, type=int)
        
        if not usernames:
            # Si no se especifican usuarios, obtener los más activos
            top_users = users_service.get_user_activity(date_range, limit=limit)
            usernames = [user['username'] for user in top_users]
        
        logger.info(f"Obteniendo evolución de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        evolution_data = users_service.get_user_evolution(date_range, usernames)
        logger.debug(f"Datos obtenidos para {len(evolution_data)} usuarios")
        
        return jsonify({
            'success': True,
            'data': evolution_data
        })
    except Exception as e:
        logger.error(f"Error al obtener evolución de usuarios: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500