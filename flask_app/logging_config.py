import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from datetime import datetime

def setup_logging(app):
    """
    Configura el sistema de logging para la aplicación Flask
    
    Args:
        app: Instancia de Flask
    """
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configurar formato de logs
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # Archivo de log principal
    main_handler = RotatingFileHandler(
        'logs/flask_app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    main_handler.setFormatter(formatter)
    main_handler.setLevel(logging.INFO)
    
    # Archivo de log para errores
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Archivo de log para accesos
    access_handler = RotatingFileHandler(
        'logs/access.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    access_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(remote_addr)s - %(method)s %(url)s %(status)s'
    ))
    access_handler.setLevel(logging.INFO)
    
    # Configurar handlers
    app.logger.addHandler(main_handler)
    app.logger.addHandler(error_handler)
    
    # Configurar nivel de logging según el modo
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)
        
        # En producción, añadir handler de email para errores críticos
        if app.config.get('MAIL_SERVER'):
            auth = None
            if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
                auth = (app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD'))
            
            secure = None
            if app.config.get('MAIL_USE_TLS'):
                secure = ()
            
            mail_handler = SMTPHandler(
                mailhost=(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT', 25)),
                fromaddr=f"no-reply@{app.config.get('MAIL_SERVER')}",
                toaddrs=app.config.get('ADMINS', []),
                subject='Error en Ukraine Crisis Twitter Analysis',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(formatter)
            app.logger.addHandler(mail_handler)
    
    # Logging de requests
    @app.before_request
    def before_request():
        """Log antes de cada request"""
        app.logger.info('Nueva petición recibida')
    
    @app.after_request
    def after_request(response):
        """Log después de cada request"""
        # Preparar datos para el log de acceso
        log_data = {
            'remote_addr': request.remote_addr,
            'method': request.method,
            'url': request.url,
            'status': response.status_code
        }
        
        # Log en archivo de acceso
        access_handler.handle(
            logging.LogRecord(
                'access', 
                logging.INFO,
                request.path,
                0,
                "%(remote_addr)s - %(method)s %(url)s %(status)s",
                log_data,
                None
            )
        )
        
        return response
    
    # Configurar manejo de errores no capturados
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Log de excepciones no capturadas"""
        app.logger.error(f'Excepción no capturada: {str(error)}', exc_info=True)
        return render_template('errors/500.html'), 500

def log_to_file(message, level=logging.INFO, **extra):
    """
    Función de utilidad para escribir logs con información adicional
    
    Args:
        message: Mensaje a loggear
        level: Nivel de logging (default: INFO)
        **extra: Datos adicionales para el log
    """
    logger = logging.getLogger('flask_app')
    
    # Añadir timestamp si no está presente
    if 'timestamp' not in extra:
        extra['timestamp'] = datetime.utcnow().isoformat()
    
    logger.log(level, message, extra=extra)

def log_to_db(message, level=logging.INFO, **extra):
    """
    Función de utilidad para escribir logs en MongoDB
    
    Args:
        message: Mensaje a loggear
        level: Nivel de logging (default: INFO)
        **extra: Datos adicionales para el log
    """
    from flask import current_app
    
    try:
        # Añadir timestamp si no está presente
        if 'timestamp' not in extra:
            extra['timestamp'] = datetime.utcnow()
        
        # Preparar documento de log
        log_doc = {
            'message': message,
            'level': level,
            'timestamp': extra.pop('timestamp'),
            'data': extra
        }
        
        # Insertar en MongoDB
        current_app.mongo.db.logs.insert_one(log_doc)
        
    except Exception as e:
        # Si falla el log a DB, escribir a archivo
        log_to_file(
            f"Error al escribir log en DB: {str(e)}",
            level=logging.ERROR,
            original_message=message,
            original_data=extra
        )

class MongoDBHandler(logging.Handler):
    """Handler personalizado para escribir logs en MongoDB"""
    
    def __init__(self, collection_name='logs'):
        """
        Inicializa el handler
        
        Args:
            collection_name: Nombre de la colección en MongoDB
        """
        super().__init__()
        self.collection_name = collection_name
    
    def emit(self, record):
        """
        Escribe el registro en MongoDB
        
        Args:
            record: Registro de logging
        """
        try:
            from flask import current_app
            
            # Preparar documento
            log_doc = {
                'timestamp': datetime.utcnow(),
                'level': record.levelname,
                'module': record.module,
                'message': record.getMessage(),
                'path': record.pathname,
                'line_no': record.lineno
            }
            
            # Añadir stack trace si hay excepción
            if record.exc_info:
                log_doc['exc_info'] = logging.Formatter().formatException(record.exc_info)
            
            # Añadir datos extra
            if hasattr(record, 'extra'):
                log_doc['extra'] = record.extra
            
            # Insertar en MongoDB
            current_app.mongo.db[self.collection_name].insert_one(log_doc)
            
        except Exception as e:
            # Fallback a stderr
            import sys
            print(f"Error al escribir log en MongoDB: {str(e)}", file=sys.stderr)