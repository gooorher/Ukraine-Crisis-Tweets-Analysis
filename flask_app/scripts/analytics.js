const { MongoClient } = require('mongodb');
const config = require('../config/mongodb.config');

class UkraineCrisisAnalytics {
  constructor(client, db) {
    this.client = client;
    this.db = db;
    this.tweets = db.collection(config.collections.tweets.name);
    this.users = db.collection(config.collections.users.name);
  }

  // Análisis de sentimiento temporal
  async getSentimentTrends(startDate, endDate, interval = 'day') {
    const timeGroup = {
      'hour': { $hour: '$tweetcreatedts' },
      'day': { $dayOfMonth: '$tweetcreatedts' },
      'week': { $week: '$tweetcreatedts' },
      'month': { $month: '$tweetcreatedts' }
    };

    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate }
        }
      },
      {
        $group: {
          _id: {
            year: { $year: '$tweetcreatedts' },
            [interval]: timeGroup[interval]
          },
          tweet_count: { $sum: 1 },
          total_engagement: { $sum: { $add: ['$retweetcount', '$favorite_count'] } },
          tweets: { $push: '$text' }
        }
      },
      { $sort: { '_id.year': 1, [`_id.${interval}`]: 1 } }
    ]).toArray();
  }

  // Análisis de hashtags trending
  async getTrendingHashtags(startDate, endDate, limit = 10) {
    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate },
          hashtags: { $exists: true, $ne: [] }
        }
      },
      { $unwind: '$hashtags' },
      {
        $group: {
          _id: '$hashtags',
          count: { $sum: 1 },
          engagement: { $sum: { $add: ['$retweetcount', '$favorite_count'] } }
        }
      },
      { $sort: { count: -1 } },
      { $limit: limit }
    ]).toArray();
  }

  // Análisis de usuarios influyentes
  async getInfluentialUsers(startDate, endDate, limit = 10) {
    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate }
        }
      },
      {
        $group: {
          _id: '$userid',
          username: { $first: '$username' },
          tweet_count: { $sum: 1 },
          total_retweets: { $sum: '$retweetcount' },
          total_favorites: { $sum: '$favorite_count' },
          avg_engagement: {
            $avg: { $add: ['$retweetcount', '$favorite_count'] }
          }
        }
      },
      {
        $lookup: {
          from: 'users',
          localField: '_id',
          foreignField: '_id',
          as: 'user_info'
        }
      },
      { $unwind: '$user_info' },
      {
        $project: {
          username: 1,
          tweet_count: 1,
          total_retweets: 1,
          total_favorites: 1,
          avg_engagement: 1,
          followers: '$user_info.followers',
          following: '$user_info.following',
          influence_score: {
            $multiply: [
              '$avg_engagement',
              { $divide: ['$user_info.followers', { $add: ['$user_info.followers', 1] }] }
            ]
          }
        }
      },
      { $sort: { influence_score: -1 } },
      { $limit: limit }
    ]).toArray();
  }

  // Análisis geográfico
  async getGeographicDistribution(startDate, endDate) {
    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate },
          'location': { $exists: true, $ne: '' }
        }
      },
      {
        $group: {
          _id: '$location',
          tweet_count: { $sum: 1 },
          users: { $addToSet: '$userid' },
          engagement: { $sum: { $add: ['$retweetcount', '$favorite_count'] } }
        }
      },
      {
        $project: {
          location: '$_id',
          tweet_count: 1,
          unique_users: { $size: '$users' },
          engagement: 1,
          engagement_per_tweet: { $divide: ['$engagement', '$tweet_count'] }
        }
      },
      { $sort: { tweet_count: -1 } }
    ]).toArray();
  }

  // Análisis de idiomas
  async getLanguageDistribution(startDate, endDate) {
    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate },
          language: { $exists: true, $ne: '' }
        }
      },
      {
        $group: {
          _id: '$language',
          tweet_count: { $sum: 1 },
          total_engagement: { $sum: { $add: ['$retweetcount', '$favorite_count'] } },
          unique_users: { $addToSet: '$userid' }
        }
      },
      {
        $project: {
          language: '$_id',
          tweet_count: 1,
          total_engagement: 1,
          unique_users: { $size: '$unique_users' },
          avg_engagement: { $divide: ['$total_engagement', '$tweet_count'] }
        }
      },
      { $sort: { tweet_count: -1 } }
    ]).toArray();
  }

  // Análisis de RT y menciones
  async getInteractionNetwork(startDate, endDate, limit = 100) {
    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate },
          $or: [
            { is_retweet: true },
            { in_reply_to_user_id: { $exists: true, $ne: null } }
          ]
        }
      },
      {
        $project: {
          source_user: '$userid',
          target_user: {
            $cond: {
              if: '$is_retweet',
              then: '$original_tweet_userid',
              else: '$in_reply_to_user_id'
            }
          },
          interaction_type: {
            $cond: { if: '$is_retweet', then: 'retweet', else: 'reply' }
          },
          engagement: { $add: ['$retweetcount', '$favorite_count'] }
        }
      },
      {
        $group: {
          _id: {
            source: '$source_user',
            target: '$target_user',
            type: '$interaction_type'
          },
          count: { $sum: 1 },
          total_engagement: { $sum: '$engagement' }
        }
      },
      { $sort: { count: -1 } },
      { $limit: limit }
    ]).toArray();
  }

  // Análisis de contenido
  async getContentAnalysis(startDate, endDate) {
    return await this.tweets.aggregate([
      {
        $match: {
          tweetcreatedts: { $gte: startDate, $lte: endDate },
          text: { $exists: true, $ne: '' }
        }
      },
      {
        $project: {
          text: 1,
          engagement: { $add: ['$retweetcount', '$favorite_count'] },
          words: { $split: ['$text', ' '] },
          length: { $strLenCP: '$text' }
        }
      },
      {
        $group: {
          _id: null,
          total_tweets: { $sum: 1 },
          avg_length: { $avg: '$length' },
          avg_engagement: { $avg: '$engagement' },
          engagement_distribution: {
            $push: '$engagement'
          }
        }
      }
    ]).toArray();
  }
}

// Función para inicializar el análisis
async function initializeAnalytics() {
  try {
    const client = await MongoClient.connect(
      `mongodb://${config.connection.host}:${config.connection.port}`,
      config.connection.options
    );
    
    const db = client.db(config.connection.database);
    return new UkraineCrisisAnalytics(client, db);
    
  } catch (error) {
    console.error('Error inicializando analytics:', error);
    throw error;
  }
}

module.exports = {
  UkraineCrisisAnalytics,
  initializeAnalytics
};