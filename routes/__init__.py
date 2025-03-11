"""
Este módulo contiene todas las rutas de la aplicación Flask.
"""
from flask import render_template
import logging

# Configurar logging para las rutas
logger = logging.getLogger(__name__)

# Importar blueprints
try:
    from flask_app.routes.trends_routes import bp as trends_bp
    from flask_app.routes.hashtags_routes import bp as hashtags_bp
    from flask_app.routes.users_routes import bp as users_bp
    from flask_app.routes.geo_routes import bp as geo_bp
    from flask_app.routes.language_routes import bp as language_bp

    # Lista de todos los blueprints
    blueprints = [
        ('trends_routes', trends_bp),
        ('hashtags_routes', hashtags_bp),
        ('users_routes', users_bp),
        ('geo_routes', geo_bp),
        ('language_routes', language_bp)
    ]

    logger.info("Blueprints cargados correctamente")
except Exception as e:
    logger.error(f"Error al cargar blueprints: {str(e)}")
    raise

# Exponer los blueprints
trends_routes = trends_bp
hashtags_routes = hashtags_bp
users_routes = users_bp
geo_routes = geo_bp
language_routes = language_bp