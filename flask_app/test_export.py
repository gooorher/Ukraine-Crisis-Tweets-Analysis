import os
import json
import csv
from datetime import datetime, timedelta
from pymongo import MongoClient
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_data_export():
    """
    Prueba la funcionalidad de exportación de datos
    """
    try:
        # Conectar a MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client.ukraine_crisis
        
        # Definir rango de fechas específico
        start_date = datetime(2022, 2, 14, 0, 0, 0)  # 14 de febrero de 2022 00:00:00
        end_date = datetime(2022, 2, 15, 23, 59, 59)  # 15 de febrero de 2022 23:59:59
        
        logger.info(f"Exportando datos para el rango: {start_date} - {end_date}")
        
        # Verificar datos disponibles en ese rango
        count = db.tweets.count_documents({
            'tweetcreatedts': {
                '$gte': start_date,
                '$lte': end_date
            }
        })
        logger.info(f"Tweets encontrados en el rango: {count:,}")
        
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
                                'format': '%Y-%m-%d %H:00:00',
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
        
        # Obtener resultados
        results = list(db.tweets.aggregate(pipeline))
        if not results:
            logger.error("No se encontraron datos para exportar")
            return False
            
        # Formatear resultados
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
            
        logger.info(f"Resultados obtenidos por hora: {len(formatted_results)}")
        
        # Mostrar todos los resultados
        logger.info("\nDesglose por hora:")
        for result in formatted_results:
            logger.info(f"Hora: {result['date']}")
            logger.info(f"  - Tweets: {result['tweet_count']:,}")
            logger.info(f"  - Engagement total: {result['total_engagement']:,}")
            logger.info(f"  - Usuarios únicos: {result['unique_users']:,}")
            logger.info(f"  - Engagement promedio: {result['avg_engagement']:.2f}")
        
        # Exportar a CSV
        csv_filename = f'trends_2022-02-14_15.csv'
        logger.info(f"\nExportando a CSV: {csv_filename}")
        
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['date', 'tweet_count', 'total_engagement', 'unique_users', 'avg_engagement']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in formatted_results:
                writer.writerow(row)
                
        # Verificar archivo CSV
        if os.path.exists(csv_filename):
            file_size = os.path.getsize(csv_filename)
            logger.info(f"Archivo CSV creado correctamente ({file_size:,} bytes)")
            
        # Exportar a JSON
        json_filename = f'trends_2022-02-14_15.json'
        logger.info(f"\nExportando a JSON: {json_filename}")
        
        with open(json_filename, 'w') as jsonfile:
            json.dump(formatted_results, jsonfile, indent=2)
            
        # Verificar archivo JSON
        if os.path.exists(json_filename):
            file_size = os.path.getsize(json_filename)
            logger.info(f"Archivo JSON creado correctamente ({file_size:,} bytes)")
            
        return True
        
    except Exception as e:
        logger.error(f"Error durante la exportación: {str(e)}")
        return False

if __name__ == '__main__':
    logger.info("Iniciando prueba de exportación...")
    
    if test_data_export():
        logger.info("✅ Prueba de exportación completada exitosamente")
        exit(0)
    else:
        logger.error("❌ La prueba de exportación falló")
        exit(1)