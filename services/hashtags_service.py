from flask import current_app
from datetime import datetime, timedelta
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

def get_hashtag_frequency(date_range, limit=20):
    """
    Obtiene la frecuencia de uso de hashtags en el rango de fechas especificado
    
    Args:
        date_range (dict): Diccionario con las fechas de inicio y fin
        limit (int): Número máximo de hashtags a retornar
        
    Returns:
        list: Lista de diccionarios con los hashtags más frecuentes y su conteo
    """
    try:
        db = get_db()
        logger.info(f"Consultando frecuencia de hashtags para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    },
                    'hashtags': {'$exists': True, '$ne': []}
                }
            },
            {'$unwind': '$hashtags'},
            {
                '$group': {
                    '_id': '$hashtags',
                    'count': {'$sum': 1},
                    'total_engagement': {'$sum': {'$add': ['$retweetcount', '$favorite_count']}}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]
        
        results = list(db.tweets.aggregate(pipeline))
        
        # Formatear resultados
        hashtag_frequency = []
        for result in results:
            hashtag_frequency.append({
                'hashtag': result['_id'],
                'count': result['count'],
                'engagement': result['total_engagement'],
                'avg_engagement': round(result['total_engagement'] / result['count'], 2)
            })
        
        logger.debug(f"Se encontraron {len(hashtag_frequency)} hashtags")
        return hashtag_frequency
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener frecuencia de hashtags: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener frecuencia de hashtags: {str(e)}\n{traceback.format_exc()}")
        raise

def get_hashtag_popularity_over_time(date_range, top_hashtags=None, limit=5):
    """
    Obtiene la evolución temporal de la popularidad de los hashtags más usados o específicos
    
    Args:
        date_range (dict): Diccionario con las fechas de inicio y fin
        top_hashtags (list): Lista de hashtags específicos a analizar. Si es None, se usan los más frecuentes
        limit (int): Número de hashtags a incluir si no se especifican hashtags
        
    Returns:
        dict: Diccionario con series temporales para cada hashtag
    """
    try:
        db = get_db()
        logger.info(f"Consultando evolución de hashtags para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        # Si no se especifican hashtags, obtener los más frecuentes
        if not top_hashtags:
            top_hashtags = [h['hashtag'] for h in get_hashtag_frequency(date_range, limit=limit)]
            
        logger.debug(f"Analizando hashtags: {top_hashtags}")
        
        # Crear pipeline para obtener datos diarios
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    },
                    'hashtags': {'$in': top_hashtags}
                }
            },
            {'$unwind': '$hashtags'},
            {
                '$match': {
                    'hashtags': {'$in': top_hashtags}
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
                        },
                        'hashtag': '$hashtags'
                    },
                    'count': {'$sum': 1},
                    'total_engagement': {'$sum': {'$add': ['$retweetcount', '$favorite_count']}}
                }
            },
            {'$sort': {'_id.date': 1}}
        ]
        
        results = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Se obtuvieron {len(results)} puntos de datos")
        
        # Generar fechas para el rango completo
        date_range_days = []
        current_date = date_range['start_date'].replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date_range['end_date'].replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current_date <= end_date:
            date_range_days.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
            
        # Formatear resultados y llenar días sin datos
        popularity_data = {hashtag: [] for hashtag in top_hashtags}
        date_data = {hashtag: {date: {'count': 0, 'engagement': 0} for date in date_range_days} 
                    for hashtag in top_hashtags}
        
        # Llenar con datos reales
        for result in results:
            hashtag = result['_id']['hashtag']
            date = result['_id']['date']
            if hashtag in date_data and date in date_data[hashtag]:
                date_data[hashtag][date] = {
                    'count': result['count'],
                    'engagement': result['total_engagement']
                }
        
        # Convertir a lista ordenada por fecha
        for hashtag in top_hashtags:
            for date in date_range_days:
                data = date_data[hashtag][date]
                popularity_data[hashtag].append({
                    'date': date,
                    'count': data['count'],
                    'engagement': data['engagement']
                })
        
        logger.debug(f"Datos procesados para {len(popularity_data)} hashtags")
        return popularity_data
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener evolución de hashtags: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener evolución de hashtags: {str(e)}\n{traceback.format_exc()}")
        raise

def get_hashtag_cooccurrence(date_range, min_occurrences=10):
    """
    Obtiene la red de co-ocurrencia de hashtags
    
    Args:
        date_range (dict): Diccionario con las fechas de inicio y fin
        min_occurrences (int): Número mínimo de co-ocurrencias para incluir una relación
        
    Returns:
        dict: Diccionario con nodos y enlaces de la red de co-ocurrencia
    """
    try:
        db = get_db()
        logger.info(f"Consultando co-ocurrencia de hashtags para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        # Primero obtener tweets con múltiples hashtags
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    },
                    'hashtags': {'$exists': True, '$not': {'$size': 0}}
                }
            },
            {'$project': {'hashtags': 1}}
        ]
        
        tweets_with_hashtags = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Se encontraron {len(tweets_with_hashtags)} tweets con hashtags")
        
        # Procesar co-ocurrencias
        cooccurrence = {}
        node_weights = {}
        
        for tweet in tweets_with_hashtags:
            hashtags = tweet.get('hashtags', [])
            if len(hashtags) > 1:
                # Actualizar peso de nodos
                for hashtag in hashtags:
                    if hashtag not in node_weights:
                        node_weights[hashtag] = 0
                    node_weights[hashtag] += 1
                
                # Actualizar co-ocurrencias
                for i in range(len(hashtags)):
                    for j in range(i + 1, len(hashtags)):
                        pair = tuple(sorted([hashtags[i], hashtags[j]]))
                        if pair not in cooccurrence:
                            cooccurrence[pair] = 0
                        cooccurrence[pair] += 1
        
        # Filtrar por número mínimo de co-ocurrencias
        filtered_links = [
            {'source': pair[0], 
             'target': pair[1], 
             'value': count}
            for pair, count in cooccurrence.items()
            if count >= min_occurrences
        ]
        
        # Obtener nodos únicos de los enlaces filtrados
        nodes = set()
        for link in filtered_links:
            nodes.add(link['source'])
            nodes.add(link['target'])
        
        # Formatear nodos con sus pesos
        formatted_nodes = [
            {'id': node, 'weight': node_weights[node]}
            for node in nodes
        ]
        
        logger.debug(f"Red generada con {len(formatted_nodes)} nodos y {len(filtered_links)} enlaces")
        return {
            'nodes': formatted_nodes,
            'links': filtered_links
        }
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener co-ocurrencia de hashtags: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener co-ocurrencia de hashtags: {str(e)}\n{traceback.format_exc()}")
        raise