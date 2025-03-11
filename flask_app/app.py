from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Importar blueprints y manejadores de error
from flask_app.routes.trends_routes import bp as trends_bp
from flask_app.routes.hashtags_routes import bp as hashtags_bp
from flask_app.routes.users_routes import bp as users_bp
from flask_app.routes.geo_routes import bp as geo_bp
from flask_app.routes.language_routes import bp as language_bp
from flask_app.error_handlers import register_error_handlers

def create_app(test_config=None):
    """Crea y configura la aplicación Flask"""
    
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Configurar la aplicación
    if test_config is None:
        # Cargar la configuración por defecto si no estamos en modo test
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
            MONGO_URI=os.environ.get('MONGO_URI', 'mongodb://localhost:27017/ukraine_crisis'),
            DEBUG=os.environ.get('FLASK_DEBUG', True),
        )
    else:
        # Sobrescribir configuración para tests
        app.config.update(test_config)
    
    # Configurar logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/flask_app.log',
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Iniciando aplicación Flask...')
    
    # Inicializar extensiones
    mongo = PyMongo(app)
    app.mongo = mongo
    
    # Verificar conexión a MongoDB
    try:
        mongo.db.command('ping')
        app.logger.info('Conexión a MongoDB establecida correctamente')
    except Exception as e:
        app.logger.error(f'Error de conexión a MongoDB: {str(e)}')
        raise
    
    # Habilitar CORS
    CORS(app)
    
    # Registrar blueprints
    app.logger.info('Registrando blueprints...')
    app.register_blueprint(trends_bp)
    app.register_blueprint(hashtags_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(geo_bp)
    app.register_blueprint(language_bp)
    app.logger.info('Blueprints registrados correctamente')
    
    # Registrar manejadores de error
    register_error_handlers(app)
    app.logger.info('Manejadores de error registrados correctamente')
    
    # Crear índices en MongoDB si no existen
    try:
        app.logger.info('Verificando índices de MongoDB...')
        
        # Índices para la colección tweets
        # mongo.db.tweets.create_index([('tweetcreatedts', 1)]) # Comentado para evitar error de índice existente
        mongo.db.tweets.create_index([('username', 1)])
        mongo.db.tweets.create_index([('hashtags', 1)])
        
        # Índices para la colección errors (logging)
        mongo.db.errors.create_index([('timestamp', -1)])
        mongo.db.errors.create_index([('error_id', 1)], unique=True)
        
        app.logger.info('Índices de MongoDB verificados correctamente')
    except Exception as e:
        app.logger.error(f'Error al crear índices en MongoDB: {str(e)}')
        raise
    
    # Función para obtener la versión de la aplicación
    @app.context_processor
    def utility_processor():
        def get_version():
            return '1.0.0'
        
        def format_datetime(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return dict(
            get_version=get_version,
            format_datetime=format_datetime
        )
    
    # Endpoint para verificar el estado de la aplicación
    @app.route('/health')
    def health_check():
        try:
            # Verificar conexión a MongoDB
            mongo.db.command('ping')
            
            return {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': get_version(),
                'mongodb': 'connected'
            }
        except Exception as e:
            app.logger.error(f'Error en health check: {str(e)}')
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': get_version(),
                'error': str(e)
            }, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
