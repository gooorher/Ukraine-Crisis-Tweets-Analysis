const { initializeAnalytics } = require('./analytics');
const moment = require('moment');

async function runAnalysisExample() {
  try {
    console.log('Iniciando análisis de ejemplo...');
    
    const analytics = await initializeAnalytics();
    
    // Definir rango de fechas para el análisis
    const startDate = moment('2022-08-19').toDate();
    const endDate = moment('2023-05-21').toDate();
    
    // 1. Obtener tendencias de sentimiento
    console.log('\n1. Análisis de tendencias temporales:');
    const sentimentTrends = await analytics.getSentimentTrends(startDate, endDate, 'month');
    console.log('Tendencias por mes:', 
      sentimentTrends.map(trend => ({
        año: trend._id.year,
        mes: trend._id.month,
        tweets: trend.tweet_count,
        engagement: trend.total_engagement
      }))
    );

    // 2. Obtener hashtags trending
    console.log('\n2. Top 10 Hashtags:');
    const trendingHashtags = await analytics.getTrendingHashtags(startDate, endDate, 10);
    console.log('Hashtags más usados:', 
      trendingHashtags.map(tag => ({
        hashtag: tag._id,
        menciones: tag.count,
        engagement: tag.engagement
      }))
    );

    // 3. Obtener usuarios influyentes
    console.log('\n3. Top 10 Usuarios Influyentes:');
    const influentialUsers = await analytics.getInfluentialUsers(startDate, endDate, 10);
    console.log('Usuarios más influyentes:', 
      influentialUsers.map(user => ({
        username: user.username,
        tweets: user.tweet_count,
        seguidores: user.followers,
        puntuación_influencia: user.influence_score
      }))
    );

    // 4. Obtener distribución geográfica
    console.log('\n4. Distribución Geográfica:');
    const geoDistribution = await analytics.getGeographicDistribution(startDate, endDate);
    console.log('Top ubicaciones:', 
      geoDistribution.slice(0, 10).map(geo => ({
        ubicación: geo.location,
        tweets: geo.tweet_count,
        usuarios_únicos: geo.unique_users,
        engagement_promedio: geo.engagement_per_tweet
      }))
    );

    // 5. Obtener distribución por idioma
    console.log('\n5. Distribución por Idioma:');
    const langDistribution = await analytics.getLanguageDistribution(startDate, endDate);
    console.log('Distribución de idiomas:', 
      langDistribution.map(lang => ({
        idioma: lang.language,
        tweets: lang.tweet_count,
        usuarios_únicos: lang.unique_users,
        engagement_promedio: lang.avg_engagement
      }))
    );

    // 6. Obtener red de interacciones
    console.log('\n6. Red de Interacciones:');
    const interactions = await analytics.getInteractionNetwork(startDate, endDate, 10);
    console.log('Top interacciones:', 
      interactions.map(int => ({
        origen: int._id.source,
        destino: int._id.target,
        tipo: int._id.type,
        cantidad: int.count,
        engagement_total: int.total_engagement
      }))
    );

    // 7. Obtener análisis de contenido
    console.log('\n7. Análisis de Contenido:');
    const contentAnalysis = await analytics.getContentAnalysis(startDate, endDate);
    console.log('Estadísticas de contenido:', {
      total_tweets: contentAnalysis[0].total_tweets,
      longitud_promedio: contentAnalysis[0].avg_length,
      engagement_promedio: contentAnalysis[0].avg_engagement
    });

    // Cerrar conexión
    await analytics.client.close();
    console.log('\nAnálisis completado.');
    
  } catch (error) {
    console.error('Error durante el análisis:', error);
    process.exit(1);
  }
}

// Ejecutar ejemplo
runAnalysisExample().catch(console.error);