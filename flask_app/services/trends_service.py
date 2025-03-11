from flask import current_app
from datetime import datetime, timedelta
from bson import ObjectId
import logging
import traceback
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

def get_db():
    """
    Obtiene la conexión a la base de datos MongoDB
    """
    try:
        if not hasattr(current_app, 'mongo') or not current_app.mongo:
            logger.error("La extensión PyMongo no está inicializada correctamente")
            raise RuntimeError("La extensión PyMongo no está inicializada correctamente")
        
        db = current_app.mongo.db
        logger.debug("Conexión a MongoDB obtenida correctamente")
        return db
    except Exception as e:
        logger.error(f"Error al obtener la conexión a MongoDB: {str(e)}\n{traceback.format_exc()}")
        raise

def get_trends(date_range):
    """
    Obtiene las tendencias generales para el rango de fechas especificado
    """
    try:
        db = get_db()
        logger.info(f"Consultando tendencias para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$tweetcreatedts'
                            }
                        }
                    },
                    'tweet_count': {'$sum': 1},
                    'total_engagement': {'$sum': {'$add': ['$retweetcount', '$favorite_count']}},
                    'unique_users': {'$addToSet': '$userid'},
                    'avg_engagement': {'$avg': {'$add': ['$retweetcount', '$favorite_count']}}
                }
            },
            {'$sort': {'_id.date': 1}}
        ]

        logger.debug(f"Ejecutando pipeline de agregación: {pipeline}")
        results = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Resultados obtenidos: {len(results)} registros")
        
        # Formatear resultados
        trends = []
        for result in results:
            trends.append({
                'date': result['_id']['date'],
                'tweet_count': result['tweet_count'],
                'total_engagement': result['total_engagement'],
                'unique_users': len(result['unique_users']),
                'avg_engagement': round(result['avg_engagement'], 2)
            })
        
        return trends
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener tendencias: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener tendencias: {str(e)}\n{traceback.format_exc()}")
        raise

def get_tweet_volume(date_range):
    """
    Obtiene el volumen de tweets por período de tiempo
    """
    try:
        db = get_db()
        logger.info(f"Consultando volumen de tweets para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$tweetcreatedts'
                            }
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.date': 1}}
        ]
        
        logger.debug(f"Ejecutando pipeline de agregación: {pipeline}")
        results = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Resultados obtenidos: {len(results)} registros")
        
        # Formatear resultados
        volume_data = []
        for result in results:
            volume_data.append({
                'date': result['_id']['date'],
                'count': result['count']
            })
        
        return volume_data
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener volumen de tweets: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener volumen de tweets: {str(e)}\n{traceback.format_exc()}")
        raise

def get_engagement_metrics(date_range):
    """
    Obtiene métricas de engagement para el rango de fechas especificado
    """
    try:
        db = get_db()
        logger.info(f"Consultando métricas de engagement para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$tweetcreatedts'
                            }
                        }
                    },
                    'avg_engagement': {'$avg': {'$add': ['$retweetcount', '$favorite_count']}},
                    'max_engagement': {'$max': {'$add': ['$retweetcount', '$favorite_count']}},
                    'total_engagement': {'$sum': {'$add': ['$retweetcount', '$favorite_count']}}
                }
            },
            {'$sort': {'_id.date': 1}}
        ]
        
        logger.debug(f"Ejecutando pipeline de agregación: {pipeline}")
        results = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Resultados obtenidos: {len(results)} registros")
        
        # Formatear resultados
        engagement_data = []
        for result in results:
            engagement_data.append({
                'date': result['_id']['date'],
                'avg_engagement': round(result['avg_engagement'], 2),
                'max_engagement': result['max_engagement'],
                'total_engagement': result['total_engagement']
            })
        
        return engagement_data
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener métricas de engagement: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener métricas de engagement: {str(e)}\n{traceback.format_exc()}")
        raise

def get_hourly_distribution(date_range):
    """
    Obtiene la distribución de tweets por hora del día
    """
    try:
        db = get_db()
        logger.info(f"Consultando distribución horaria para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'hour': {'$hour': '$tweetcreatedts'}
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.hour': 1}}
        ]
        
        logger.debug(f"Ejecutando pipeline de agregación: {pipeline}")
        results = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Resultados obtenidos: {len(results)} registros")
        
        # Formatear resultados y asegurar que tenemos las 24 horas
        hourly_data = {i: 0 for i in range(24)}
        for result in results:
            hourly_data[result['_id']['hour']] = result['count']
        
        return [{'hour': hour, 'count': count} for hour, count in hourly_data.items()]
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener distribución horaria: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener distribución horaria: {str(e)}\n{traceback.format_exc()}")
        raise