import os
from datetime import datetime, timedelta

class Config:
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    DEBUG = True

    # Configuración de MongoDB
    MONGO_HOST = os.environ.get('MONGO_HOST') or 'localhost'
    MONGO_PORT = int(os.environ.get('MONGO_PORT') or 27017)
    MONGO_DB = os.environ.get('MONGO_DB') or 'ukraine_crisis'
    MONGO_URI = os.environ.get('MONGO_URI') or f'mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}'

    # Configuración de la aplicación
    TWEETS_PER_PAGE = int(os.environ.get('TWEETS_PER_PAGE') or 50)
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Configuración de cache
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT') or 300)  # 5 minutos

    # Configuración de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Configuración de exportación
    EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    MAX_EXPORT_ROWS = int(os.environ.get('MAX_EXPORT_ROWS') or 100000)

    # Rangos de tiempo predefinidos
    DEFAULT_START_DATE = datetime(2022, 1, 1)
    DEFAULT_END_DATE = datetime.utcnow()
    
    TIME_RANGES = {
        '1d': timedelta(days=1),
        '7d': timedelta(days=7),
        '30d': timedelta(days=30),
        '90d': timedelta(days=90),
        'all': None  # Sin límite de tiempo
    }

    # Lista de campos para exportación
    EXPORT_FIELDS = [
        'id',
        'text',
        'userid',
        'username',
        'tweetcreatedts',
        'retweetcount',
        'favorite_count',
        'followers',
        'friends',
        'language',
        'hashtags',
        'mentions'
    ]

    # Configuración de MongoDB Indexes
    MONGODB_INDEXES = [
        ('tweets', [('tweetcreatedts', 1)]),
        ('tweets', [('userid', 1)]),
        ('tweets', [('language', 1)]),
        ('tweets', [('hashtags', 1)]),
    ]

    @staticmethod
    def init_app(app):
        """Inicialización adicional de la aplicación"""
        # Crear directorio de exportación si no existe
        if not os.path.exists(Config.EXPORT_FOLDER):
            os.makedirs(Config.EXPORT_FOLDER)
            
        # Configurar los índices de MongoDB
        with app.app_context():
            db = app.mongo.db
            for collection, index in Config.MONGODB_INDEXES:
                db[collection].create_index(index)