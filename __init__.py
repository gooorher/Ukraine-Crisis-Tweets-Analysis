"""
Flask application package
"""
from flask import Flask, redirect
from flask_pymongo import PyMongo
from flask_caching import Cache
from config import Config
import logging
import sys

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    app.config['MONGO_URI'] = Config.MONGO_URI
    app.mongo = PyMongo(app)  # Store mongo instance directly on app
    app.cache = Cache(app)    # Store cache instance directly on app
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format=app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        datefmt=app.config.get('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S'),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('flask_app.log')
        ]
    )
    
    # Import blueprints
    try:
        from flask_app.routes.trends_routes import bp as trends_bp
        from flask_app.routes.hashtags_routes import bp as hashtags_bp
        from flask_app.routes.users_routes import bp as users_bp
        from flask_app.routes.geo_routes import bp as geo_bp
        from flask_app.routes.language_routes import bp as language_bp
        
        # Register blueprints
        app.register_blueprint(trends_bp)
        app.register_blueprint(hashtags_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(geo_bp)
        app.register_blueprint(language_bp)
        
        # Ruta raíz que redirige a /trends/
        # Ruta raíz que redirige a la sección de tendencias
        @app.route('/')
        def index():
            return redirect('/trends/#tendences')
        
        logger.info("Blueprints y rutas registrados correctamente")
    except Exception as e:
        logger.error(f"Error al registrar blueprints: {str(e)}")
        raise

    # Test MongoDB connection
    try:
        app.mongo.db.command('ping')
        logger.info("Conexión a MongoDB establecida correctamente")
    except Exception as e:
        logger.error(f"Error al conectar con MongoDB: {str(e)}")
        raise
    
    return app