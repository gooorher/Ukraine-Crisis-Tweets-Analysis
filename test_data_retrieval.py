from pymongo import MongoClient
from datetime import datetime, timedelta
from pprint import pprint

def test_data_queries():
    try:
        # Conectar a MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['ukraine_crisis']
        
        # 1. Contar total de tweets
        total_tweets = db.tweets.count_documents({})
        print(f"\n1. Total de tweets en la base de datos: {total_tweets:,}")

        # 2. Obtener estadísticas básicas
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
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
                    'tweet_count': {'$sum': 1},
                    'total_engagement': {'$sum': {'$add': ['$retweetcount', '$favorite_count']}},
                    'unique_users': {'$addToSet': '$userid'},
                    'avg_engagement': {'$avg': {'$add': ['$retweetcount', '$favorite_count']}}
                }
            }
        ]
        
        results = list(db.tweets.aggregate(pipeline))
        if results:
            stats = results[0]
            print("\n2. Estadísticas de los últimos 30 días:")
            print(f"   - Tweets: {stats['tweet_count']:,}")
            print(f"   - Engagement total: {stats['total_engagement']:,}")
            print(f"   - Usuarios únicos: {len(stats['unique_users']):,}")
            print(f"   - Engagement promedio: {stats['avg_engagement']:.2f}")

        # 3. Top 5 hashtags
        pipeline = [
            {'$unwind': '$hashtags'},
            {'$group': {
                '_id': '$hashtags',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        
        top_hashtags = list(db.tweets.aggregate(pipeline))
        print("\n3. Top 5 hashtags:")
        for idx, hashtag in enumerate(top_hashtags, 1):
            print(f"   {idx}. #{hashtag['_id']} ({hashtag['count']:,} menciones)")

        # 4. Distribución por idioma
        pipeline = [
            {
                '$group': {
                    '_id': '$language',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        
        lang_dist = list(db.tweets.aggregate(pipeline))
        print("\n4. Top 5 idiomas:")
        for idx, lang in enumerate(lang_dist, 1):
            print(f"   {idx}. {lang['_id']} ({lang['count']:,} tweets)")

        print("\n✅ Pruebas de consulta completadas con éxito")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nProbando consultas a MongoDB...")
    test_data_queries()