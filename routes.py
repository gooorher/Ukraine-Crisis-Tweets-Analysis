from flask import Flask

def register_routes(app):
    # Registrar las rutas de tendencias
    from .routes import trends_routes
    app.register_blueprint(trends_routes.bp)

    # Registrar las rutas de hashtags
    from .routes import hashtags_routes
    app.register_blueprint(hashtags_routes.bp)

    # Registrar las rutas de geo
    from .routes import geo_routes
    app.register_blueprint(geo_routes.bp)

    # Registrar las rutas de idiomas
    from .routes import language_routes
    app.register_blueprint(language_routes.bp)