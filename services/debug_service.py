import logging
from datetime import datetime
from pymongo import MongoClient

logger = logging.getLogger(__name__)

def debug_mongo_connection():
    """
    Realiza un diagnóstico detallado de la conexión a MongoDB y los datos disponibles
    """
    try:
        # Conectar a MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ukraine_crisis
        
        # 1. Verificar conexión
        logger.info("Verificando conexión a MongoDB...")
        db.command('ping')
        logger.info("✅ Conexión a MongoDB establecida")
        
        # 2. Verificar colecciones
        collections = db.list_collection_names()
        logger.info(f"Colecciones disponibles: {collections}")
        
        # 3. Verificar documentos en tweets
        total_tweets = db.tweets.count_documents({})
        logger.info(f"Total de tweets: {total_tweets:,}")
        
        # 4. Verificar rango de fechas
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'min_date': {'$min': '$tweetcreatedts'},
                    'max_date': {'$max': '$tweetcreatedts'}
                }
            }
        ]
        date_range = list(db.tweets.aggregate(pipeline))[0]
        logger.info(f"Rango de fechas disponible:")
        logger.info(f"  - Desde: {date_range['min_date']}")
        logger.info(f"  - Hasta: {date_range['max_date']}")
        
        # 5. Verificar muestra de datos
        sample = db.tweets.find_one()
        if sample:
            logger.info("Ejemplo de documento:")
            logger.info(f"  - ID: {sample.get('_id')}")
            logger.info(f"  - Fecha: {sample.get('tweetcreatedts')}")
            logger.info(f"  - Usuario: {sample.get('userid')}")
            logger.info(f"  - Retweets: {sample.get('retweetcount')}")
            logger.info(f"  - Favoritos: {sample.get('favorite_count')}")
        
        # 6. Verificar índices
        indices = db.tweets.list_indexes()
        logger.info("Índices configurados:")
        for index in indices:
            logger.info(f"  - {index['name']}: {index['key']}")
        
        # 7. Verificar distribución de tweets por día
        pipeline = [
            {
                '$group': {
                    '_id': {
                        'year': {'$year': '$tweetcreatedts'},
                        'month': {'$month': '$tweetcreatedts'},
                        'day': {'$dayOfMonth': '$tweetcreatedts'}
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': -1}},
            {'$limit': 5}
        ]
        daily_counts = list(db.tweets.aggregate(pipeline))
        logger.info("Últimos 5 días con datos:")
        for day in daily_counts:
            date = f"{day['_id']['year']}-{day['_id']['month']:02d}-{day['_id']['day']:02d}"
            logger.info(f"  - {date}: {day['count']:,} tweets")
        
        return True
        
    except Exception as e:
        logger.error(f"Error durante el diagnóstico: {str(e)}")
        return False

def debug_data_processing():
    """
    Realiza un diagnóstico del procesamiento de datos
    """
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ukraine_crisis
        
        # Definir un rango de prueba (último día con datos)
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'max_date': {'$max': '$tweetcreatedts'}
                }
            }
        ]
        max_date = list(db.tweets.aggregate(pipeline))[0]['max_date']
        start_date = max_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        logger.info(f"Probando procesamiento para el día {start_date.date()}")
        
        # 1. Contar tweets
        tweet_count = db.tweets.count_documents({
            'tweetcreatedts': {
                '$gte': start_date,
                '$lte': end_date
            }
        })
        logger.info(f"Tweets en el período: {tweet_count:,}")
        
        # 2. Calcular métricas
        pipeline = [
            {
                '$match': {
                    'tweetcreatedts': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_engagement': {'$sum': {'$add': ['$retweetcount', '$favorite_count']}},
                    'unique_users': {'$addToSet': '$userid'},
                    'avg_engagement': {'$avg': {'$add': ['$retweetcount', '$favorite_count']}}
                }
            }
        ]
        
        metrics = list(db.tweets.aggregate(pipeline))[0]
        logger.info("Métricas calculadas:")
        logger.info(f"  - Engagement total: {metrics['total_engagement']:,}")
        logger.info(f"  - Usuarios únicos: {len(metrics['unique_users']):,}")
        logger.info(f"  - Engagement promedio: {metrics['avg_engagement']:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error durante el diagnóstico de procesamiento: {str(e)}")
        return False

if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Iniciando diagnóstico...")
    
    if debug_mongo_connection() and debug_data_processing():
        logger.info("✅ Diagnóstico completado exitosamente")
        exit(0)
    else:
        logger.error("❌ El diagnóstico encontró problemas")
        exit(1)