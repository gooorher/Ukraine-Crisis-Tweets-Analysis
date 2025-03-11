from flask import render_template, current_app, request
import logging
from uuid import uuid4
from datetime import datetime
import traceback
import json

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Registra todos los manejadores de error para la aplicación"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Maneja errores 404 - Página no encontrada"""
        error_id = str(uuid4())
        logger.warning(f'Error 404: {request.url} - Error ID: {error_id}')
        
        return render_template('errors/404.html',
            error_id=error_id,
            timestamp=datetime.utcnow().isoformat(),
            debug=app.debug
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Maneja errores 500 - Error interno del servidor"""
        error_id = str(uuid4())
        logger.error(f'Error 500: {str(error)} - Error ID: {error_id}\n{traceback.format_exc()}')
        
        return render_template('errors/500.html',
            error_id=error_id,
            error_message=str(error),
            timestamp=datetime.utcnow().isoformat(),
            debug=app.debug
        ), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        """Maneja excepciones no capturadas"""
        error_id = str(uuid4())
        logger.error(f'Excepción no capturada: {str(error)} - Error ID: {error_id}\n{traceback.format_exc()}')
        
        return render_template('errors/500.html',
            error_id=error_id,
            error_message=str(error),
            timestamp=datetime.utcnow().isoformat(),
            debug=app.debug
        ), 500

    def handle_section_error(error, section):
        """
        Maneja errores específicos de sección (trends, hashtags, users)
        
        Args:
            error: La excepción o error ocurrido
            section: Nombre de la sección ('trends', 'hashtags', 'users')
        """
        error_id = str(uuid4())
        logger.error(f'Error en {section}: {str(error)} - Error ID: {error_id}\n{traceback.format_exc()}')
        
        debug_info = None
        if app.debug:
            debug_info = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'request': {
                    'path': request.path,
                    'method': request.method,
                    'args': dict(request.args),
                    'headers': dict(request.headers)
                }
            }
        
        return render_template(f'errors/{section}_error.html',
            error_id=error_id,
            error_message=str(error),
            timestamp=datetime.utcnow().isoformat(),
            debug=app.debug,
            debug_info=json.dumps(debug_info, indent=2) if debug_info else None
        ), 500

    @app.errorhandler(TrendsError)
    def handle_trends_error(error):
        """Maneja errores específicos de la sección de tendencias"""
        return handle_section_error(error, 'trends')

    @app.errorhandler(HashtagsError)
    def handle_hashtags_error(error):
        """Maneja errores específicos de la sección de hashtags"""
        return handle_section_error(error, 'hashtags')

    @app.errorhandler(UsersError)
    def handle_users_error(error):
        """Maneja errores específicos de la sección de usuarios"""
        return handle_section_error(error, 'users')

    @app.route('/api/log-error', methods=['POST'])
    def log_client_error():
        """API endpoint para registrar errores del cliente"""
        try:
            error_data = request.get_json()
            error_id = str(uuid4())
            
            logger.error(f'Error del cliente - ID: {error_id}')
            logger.error(json.dumps(error_data, indent=2))
            
            return jsonify({
                'success': True,
                'error_id': error_id
            })
        except Exception as e:
            logger.error(f'Error al registrar error del cliente: {str(e)}')
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

# Clases de error personalizadas
class AppError(Exception):
    """Clase base para errores de la aplicación"""
    pass

class TrendsError(AppError):
    """Errores específicos de la sección de tendencias"""
    pass

class HashtagsError(AppError):
    """Errores específicos de la sección de hashtags"""
    pass

class UsersError(AppError):
    """Errores específicos de la sección de usuarios"""
    pass

# Funciones auxiliares para lanzar errores
def raise_trends_error(message):
    """Lanza un error de tendencias con el mensaje especificado"""
    logger.error(f'TrendsError: {message}')
    raise TrendsError(message)

def raise_hashtags_error(message):
    """Lanza un error de hashtags con el mensaje especificado"""
    logger.error(f'HashtagsError: {message}')
    raise HashtagsError(message)

def raise_users_error(message):
    """Lanza un error de usuarios con el mensaje especificado"""
    logger.error(f'UsersError: {message}')
    raise UsersError(message)

def log_error_to_db(error_id, error_data):
    """
    Registra un error en la base de datos para análisis posterior
    
    Args:
        error_id: ID único del error
        error_data: Diccionario con los datos del error
    """
    try:
        db = current_app.mongo.db
        db.errors.insert_one({
            'error_id': error_id,
            'timestamp': datetime.utcnow(),
            'data': error_data
        })
    except Exception as e:
        logger.error(f'Error al registrar error en DB: {str(e)}')