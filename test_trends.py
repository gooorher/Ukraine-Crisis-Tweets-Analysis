from flask import Flask
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import json

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_trends_pipeline():
    """
    Prueba la pipeline de agregación de tendencias directamente contra MongoDB
    """
    try:
        # Conectar a MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ukraine_crisis
        
        # Definir rango de fechas de prueba
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        logger.info(f"Consultando tendencias para el rango: {start_date} - {end_date}")
        
        # Pipeline de agregación
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
        
        # Ejecutar pipeline
        logger.info("Ejecutando pipeline de agregación...")
        results = list(db.tweets.aggregate(pipeline))
        
        # Verificar resultados
        logger.info(f"Obtenidos {len(results)} resultados")
        
        if not results:
            logger.error("No se encontraron resultados")
            return False
            
        # Formatear y mostrar algunos resultados de ejemplo
        formatted_results = []
        for result in results:
            formatted_result = {
                'date': result['_id']['date'],
                'tweet_count': result['tweet_count'],
                'total_engagement': result['total_engagement'],
                'unique_users': len(result['unique_users']),
                'avg_engagement': round(result['avg_engagement'], 2)
            }
            formatted_results.append(formatted_result)
            
        # Mostrar los primeros 5 resultados
        logger.info("Primeros 5 resultados:")
        print(json.dumps(formatted_results[:5], indent=2))
        
        # Guardar resultados en un archivo para análisis
        with open('trends_test_results.json', 'w') as f:
            json.dump(formatted_results, f, indent=2)
        logger.info("Resultados guardados en trends_test_results.json")
        
        return True
        
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
        return False

def test_date_ranges():
    """
    Prueba diferentes rangos de fechas para verificar la disponibilidad de datos
    """
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ukraine_crisis
        
        # Probar diferentes rangos
        ranges = [
            ('Últimos 7 días', 7),
            ('Últimos 30 días', 30),
            ('Últimos 90 días', 90)
        ]
        
        for range_name, days in ranges:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            count = db.tweets.count_documents({
                'tweetcreatedts': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            })
            
            logger.info(f"{range_name}: {count:,} tweets encontrados")
            
        return True
        
    except Exception as e:
        logger.error(f"Error probando rangos de fechas: {str(e)}")
        return False

def test_data_format():
    """
    Verifica el formato de los datos en la colección de tweets
    """
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ukraine_crisis
        
        # Obtener un tweet de ejemplo
        tweet = db.tweets.find_one()
        
        if not tweet:
            logger.error("No se encontraron tweets")
            return False
            
        # Verificar campos requeridos
        required_fields = ['tweetcreatedts', 'userid', 'retweetcount', 'favorite_count']
        missing_fields = [field for field in required_fields if field not in tweet]
        
        if missing_fields:
            logger.error(f"Campos faltantes en los tweets: {missing_fields}")
            return False
            
        # Verificar tipo de datos
        if not isinstance(tweet['tweetcreatedts'], datetime):
            logger.error("El campo tweetcreatedts no es de tipo datetime")
            return False
            
        logger.info("Formato de datos verificado correctamente")
        logger.debug(f"Ejemplo de tweet: {tweet}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando formato de datos: {str(e)}")
        return False

if __name__ == '__main__':
    logger.info("Iniciando pruebas de la sección de tendencias...")
    
    # Ejecutar todas las pruebas
    tests = [
        ('Pipeline de tendencias', test_trends_pipeline),
        ('Rangos de fechas', test_date_ranges),
        ('Formato de datos', test_data_format)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        logger.info(f"\nEjecutando prueba: {test_name}")
        if test_func():
            logger.info(f"✅ {test_name}: OK")
        else:
            logger.error(f"❌ {test_name}: FAILED")
            all_passed = False
            
    if all_passed:
        logger.info("\n✅ Todas las pruebas pasaron correctamente")
        exit(0)
    else:
        logger.error("\n❌ Algunas pruebas fallaron")
        exit(1)