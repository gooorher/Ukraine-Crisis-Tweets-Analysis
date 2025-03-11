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

def get_user_activity(date_range, limit=20):
    """
    Obtiene los usuarios más activos en el rango de fechas especificado
    """
    try:
        db = get_db()
        logger.info(f"Consultando actividad de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
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
                    '_id': '$userid',
                    'username': {'$first': '$username'},
                    'tweet_count': {'$sum': 1},
                    'total_engagement': {
                        '$sum': {'$add': ['$retweetcount', '$favorite_count']}
                    },
                    'followers': {'$first': '$followers_count'},
                    'following': {'$first': '$following_count'}
                }
            },
            {'$sort': {'tweet_count': -1}},
            {'$limit': limit}
        ]
        
        results = list(db.tweets.aggregate(pipeline))
        
        # Formatear resultados
        activity_data = []
        for result in results:
            activity_data.append({
                'user_id': result['_id'],
                'username': result['username'],
                'tweet_count': result['tweet_count'],
                'engagement': result['total_engagement'],
                'followers': result['followers'],
                'following': result['following'],
                'engagement_rate': round(result['total_engagement'] / result['tweet_count'], 2)
            })
        
        return activity_data
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener actividad de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener actividad de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise

def get_user_engagement(date_range, limit=20):
    """
    Obtiene los usuarios con sus métricas de influencia y seguidores en el rango de fechas especificado
    """
    try:
        db = get_db()
        logger.info(f"Consultando métricas de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
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
                    '_id': '$userid',
                    'username': {'$first': '$username'},
                    'tweet_count': {'$sum': 1},
                    'retweets': {'$sum': '$retweetcount'},
                    'favorites': {'$sum': '$favorite_count'},
                    'followers': {'$first': '$followers_count'},
                    'following': {'$first': '$following_count'},
                    'verified': {'$first': '$verified'}
                }
            },
            {
                '$addFields': {
                    'total_engagement': {'$add': ['$retweets', '$favorites']},
                    'influence_score': {
                        '$cond': {
                            'if': {'$eq': ['$tweet_count', 0]},
                            'then': 0,
                            'else': {
                                '$multiply': [
                                    {'$divide': ['$total_engagement', '$tweet_count']},
                                    {'$ln': {'$add': ['$followers', 1]}}
                                ]
                            }
                        }
                    }
                }
            },
            {'$sort': {'followers': -1}},
            {'$limit': limit}
        ]
        
        results = list(db.tweets.aggregate(pipeline))
        
        # Formatear resultados
        users_data = []
        for result in results:
            # Asegurar que influence_score no sea None
            influence_score = result.get('influence_score', 0)
            if influence_score is None:
                influence_score = 0
                
            users_data.append({
                'user_id': result['_id'],
                'username': result['username'],
                'followers': result['followers'],
                'influence_score': round(influence_score, 2),
                'verified': result.get('verified', False)
            })
        
        return users_data
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener engagement de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener engagement de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise

def get_user_influence(date_range, limit=20):
    """
    Obtiene los usuarios más influyentes en el rango de fechas especificado
    """
    try:
        db = get_db()
        logger.info(f"Consultando influencia de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        # Primer pipeline para obtener estadísticas básicas
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
                    '_id': '$userid',
                    'username': {'$first': '$username'},
                    'tweet_count': {'$sum': 1},
                    'retweets': {'$sum': {'$cond': [{'$gt': ['$retweetcount', 0]}, '$retweetcount', 0]}},
                    'favorites': {'$sum': {'$cond': [{'$gt': ['$favorite_count', 0]}, '$favorite_count', 0]}},
                    'followers': {
                        '$first': {
                            '$cond': [
                                {'$gt': ['$followers_count', 0]},
                                '$followers_count',
                                0
                            ]
                        }
                    },
                    'following': {
                        '$first': {
                            '$cond': [
                                {'$gt': ['$following_count', 0]},
                                '$following_count',
                                0
                            ]
                        }
                    },
                    'verified': {'$first': '$verified'}
                }
            },
            {
                '$addFields': {
                    'total_engagement': {'$add': ['$retweets', '$favorites']},
                    'engagement_rate': {
                        '$cond': {
                            'if': {'$eq': ['$tweet_count', 0]},
                            'then': 0,
                            'else': {
                                '$divide': [
                                    {'$add': ['$retweets', '$favorites']},
                                    {'$cond': [{'$gt': ['$tweet_count', 0]}, '$tweet_count', 1]}
                                ]
                            }
                        }
                    }
                }
            },
            {
                '$match': {
                    'tweet_count': {'$gt': 0}
                }
            }
        ]
        
        logger.debug(f"Ejecutando pipeline de agregación para el rango: {date_range}")
        initial_results = list(db.tweets.aggregate(pipeline))
        logger.debug(f"Resultados iniciales obtenidos: {len(initial_results)} usuarios")
        
        # Establecer valores por defecto para normalización
        max_engagement = 1  # Evitar división por cero
        max_followers = 1   # Evitar división por cero
        
        # Calculate max values safely
        # Procesar resultados y calcular métricas
        if not initial_results:
            logger.warning("No se encontraron resultados para el rango de fechas especificado")
            return []

        # Inicializar arrays para métricas
        engagement_rates = []
        followers_counts = []
        logger.info(f"Procesando datos para {len(initial_results)} usuarios")
            
        for r in initial_results:
            # Validar y obtener engagement_rate
            if 'engagement_rate' not in r:
                logger.warning(f"Usuario {r['username']} sin engagement_rate calculado")
                r['engagement_rate'] = r['total_engagement'] / r['tweet_count'] if r['tweet_count'] > 0 else 0
            
            # Asegurar valores válidos
            engagement_rate = r['engagement_rate'] if r['engagement_rate'] is not None else 0
            engagement_rates.append(engagement_rate)
            
            followers = r['followers'] if r['followers'] is not None else 0
            followers_counts.append(followers)
            
            # Log detallado por usuario
            logger.debug(
                f"Métricas para {r['username']}: "
                f"tweets={r['tweet_count']}, "
                f"retweets={r.get('retweets', 0)}, "
                f"favorites={r.get('favorites', 0)}, "
                f"total_engagement={r['total_engagement']}, "
                f"engagement_rate={engagement_rate:.2f}, "
                f"followers={followers}"
            )
        
        # Calcular y validar valores máximos
        max_engagement = max(engagement_rates) if engagement_rates else 1
        max_followers = max(followers_counts) if followers_counts else 1
        
        logger.info(
            f"Estadísticas globales:\n"
            f"- Usuarios procesados: {len(initial_results)}\n"
            f"- Max engagement rate: {max_engagement:.2f}\n"
            f"- Max followers: {max_followers}\n"
            f"- Promedio engagement: {sum(engagement_rates)/len(engagement_rates):.2f}\n"
            f"- Promedio followers: {sum(followers_counts)/len(followers_counts):.2f}"
        )
        
        # Calcular influence_score normalizado
        influence_data = []
        for result in initial_results:
            try:
                # Obtener y validar valores
                engagement_rate = float(result.get('engagement_rate', 0) or 0)
                followers = int(result.get('followers', 0) or 0)
                tweets = int(result.get('tweet_count', 0) or 0)
                
                # Normalizar métricas
                norm_engagement = engagement_rate / max_engagement if max_engagement > 0 else 0
                norm_followers = followers / max_followers if max_followers > 0 else 0
                
                # Calcular score con pesos ajustados
                engagement_weight = 0.7
                followers_weight = 0.3
                
                raw_score = (engagement_weight * norm_engagement +
                           followers_weight * norm_followers) * 100
                
                # Aplicar límites y redondeo
                influence_score = min(100, round(raw_score, 2))
                
                logger.debug(
                    f"Cálculo de influencia para {result['username']}:\n"
                    f"- Tweets: {tweets}\n"
                    f"- Engagement: {engagement_rate:.2f} (norm: {norm_engagement:.3f})\n"
                    f"- Followers: {followers} (norm: {norm_followers:.3f})\n"
                    f"- Raw score: {raw_score:.2f}\n"
                    f"- Final score: {influence_score}"
                )
                
                if influence_score > 0:
                    influence_data.append({
                        'user_id': result['_id'],
                        'username': result['username'],
                        'tweet_count': tweets,
                        'engagement': result['total_engagement'],
                        'engagement_rate': round(engagement_rate, 2),
                        'followers': followers,
                        'following': result.get('following', 0),
                        'verified': result.get('verified', False),
                        'influence_score': influence_score
                    })
            except Exception as e:
                logger.error(f"Error procesando usuario {result.get('username', 'desconocido')}: {str(e)}")
                continue
        
        # Ordenar por influence_score y limitar resultados
        influence_data.sort(key=lambda x: x['influence_score'], reverse=True)
        influence_data = influence_data[:limit]
        
        logger.info(f"Procesamiento completado. Retornando {len(influence_data)} usuarios más influyentes")
        
        return influence_data
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener influencia de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener influencia de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise

def get_user_details(username, date_range):
    """
    Obtiene detalles específicos de un usuario
    """
    try:
        db = get_db()
        logger.info(f"Consultando detalles del usuario {username} para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'username': username,
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    }
                }
            },
            {
                '$group': {
                    '_id': '$userid',
                    'username': {'$first': '$username'},
                    'tweet_count': {'$sum': 1},
                    'retweets': {'$sum': '$retweetcount'},
                    'favorites': {'$sum': '$favorite_count'},
                    'followers': {'$first': '$followers_count'},
                    'following': {'$first': '$following_count'},
                    'verified': {'$first': '$verified'},
                    'created_at': {'$first': '$user_created'},
                    'tweets': {
                        '$push': {
                            'text': '$text',
                            'created_at': '$tweetcreatedts',
                            'retweets': '$retweetcount',
                            'favorites': '$favorite_count'
                        }
                    }
                }
            }
        ]
        
        result = list(db.tweets.aggregate(pipeline))
        
        if not result:
            return None
            
        user_data = result[0]
        
        # Formatear resultado
        return {
            'user_id': user_data['_id'],
            'username': user_data['username'],
            'tweet_count': user_data['tweet_count'],
            'retweets': user_data['retweets'],
            'favorites': user_data['favorites'],
            'followers': user_data['followers'],
            'following': user_data['following'],
            'verified': user_data.get('verified', False),
            'created_at': user_data['created_at'],
            'engagement_rate': round((user_data['retweets'] + user_data['favorites']) / user_data['tweet_count'], 2),
            'recent_tweets': sorted(user_data['tweets'], key=lambda x: x['created_at'], reverse=True)[:10]
        }
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener detalles del usuario: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener detalles del usuario: {str(e)}\n{traceback.format_exc()}")
        raise

def get_user_evolution(date_range, usernames):
    """
    Obtiene la evolución temporal de métricas para usuarios específicos
    """
    try:
        db = get_db()
        logger.info(f"Consultando evolución de usuarios para el rango: {date_range['start_date']} - {date_range['end_date']}")
        
        pipeline = [
            {
                '$match': {
                    'username': {'$in': usernames},
                    'tweetcreatedts': {
                        '$gte': date_range['start_date'],
                        '$lte': date_range['end_date']
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'username': '$username',
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$tweetcreatedts'
                            }
                        }
                    },
                    'tweet_count': {'$sum': 1},
                    'engagement': {
                        '$sum': {'$add': ['$retweetcount', '$favorite_count']}
                    }
                }
            },
            {'$sort': {'_id.date': 1}}
        ]
        
        results = list(db.tweets.aggregate(pipeline))
        
        # Formatear resultados por usuario
        evolution_data = {}
        for result in results:
            username = result['_id']['username']
            if username not in evolution_data:
                evolution_data[username] = []
                
            evolution_data[username].append({
                'date': result['_id']['date'],
                'tweet_count': result['tweet_count'],
                'engagement': result['engagement']
            })
            
        return evolution_data
    except PyMongoError as e:
        logger.error(f"Error de MongoDB al obtener evolución de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise
    except Exception as e:
        logger.error(f"Error al obtener evolución de usuarios: {str(e)}\n{traceback.format_exc()}")
        raise