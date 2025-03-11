const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const { MongoClient } = require('mongodb');
const config = require('../config/mongodb.config');

// Tamaño del lote para inserciones
const BATCH_SIZE = 1000;

// Función para procesar y transformar un tweet
function processTweet(rawTweet) {
  return {
    _id: rawTweet.tweetid,
    userid: rawTweet.userid,
    username: rawTweet.username,
    tweetcreatedts: new Date(rawTweet.tweetcreatedts),
    retweetcount: parseInt(rawTweet.retweetcount, 10),
    text: rawTweet.text,
    hashtags: rawTweet.hashtags ? JSON.parse(rawTweet.hashtags.replace(/'/g, '"')) : [],
    language: rawTweet.language,
    coordinates: rawTweet.coordinates ? JSON.parse(rawTweet.coordinates) : null,
    favorite_count: parseInt(rawTweet.favorite_count, 10),
    is_retweet: rawTweet.is_retweet === 'true',
    original_tweet_id: rawTweet.original_tweet_id || null,
    original_tweet_userid: rawTweet.original_tweet_userid || null,
    original_tweet_username: rawTweet.original_tweet_username || null,
    in_reply_to_status_id: rawTweet.in_reply_to_status_id || null,
    in_reply_to_user_id: rawTweet.in_reply_to_user_id || null,
    in_reply_to_screen_name: rawTweet.in_reply_to_screen_name || null,
    is_quote_status: rawTweet.is_quote_status === 'true',
    quoted_status_id: rawTweet.quoted_status_id || null,
    quoted_status_userid: rawTweet.quoted_status_userid || null,
    quoted_status_username: rawTweet.quoted_status_username || null,
    extractedts: new Date(rawTweet.extractedts)
  };
}

// Función para procesar y transformar un usuario
function processUser(rawTweet) {
  return {
    _id: rawTweet.userid,
    username: rawTweet.username,
    acctdesc: rawTweet.acctdesc,
    location: rawTweet.location,
    following: parseInt(rawTweet.following, 10),
    followers: parseInt(rawTweet.followers, 10),
    totaltweets: parseInt(rawTweet.totaltweets, 10),
    usercreatedts: new Date(rawTweet.usercreatedts)
  };
}

async function processCsvFile(filePath, db) {
  const tweets = [];
  const users = new Map(); // Usar Map para mantener usuarios únicos
  let tweetCount = 0;
  let userCount = 0;

  return new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', async (row) => {
        // Procesar tweet
        const tweet = processTweet(row);
        tweets.push(tweet);
        tweetCount++;

        // Procesar usuario si no existe
        if (!users.has(row.userid)) {
          users.set(row.userid, processUser(row));
          userCount++;
        }

        // Insertar en lotes cuando alcance BATCH_SIZE
        if (tweets.length >= BATCH_SIZE) {
          try {
            await insertBatch(db, tweets, Array.from(users.values()));
            tweets.length = 0;
            users.clear();
          } catch (error) {
            console.error(`Error insertando lote: ${error}`);
          }
        }
      })
      .on('end', async () => {
        try {
          // Insertar el último lote si queda algo
          if (tweets.length > 0) {
            await insertBatch(db, tweets, Array.from(users.values()));
          }
          console.log(`Archivo ${path.basename(filePath)} procesado:`, {
            tweets: tweetCount,
            users: userCount
          });
          resolve();
        } catch (error) {
          reject(error);
        }
      })
      .on('error', (error) => {
        reject(error);
      });
  });
}

async function insertBatch(db, tweets, users) {
  const session = db.client.startSession();
  try {
    await session.withTransaction(async () => {
      // Insertar tweets
      if (tweets.length > 0) {
        await db.collection(config.collections.tweets.name)
          .insertMany(tweets, { ordered: false });
      }

      // Insertar usuarios (upsert para evitar duplicados)
      if (users.length > 0) {
        const ops = users.map(user => ({
          updateOne: {
            filter: { _id: user._id },
            update: { $set: user },
            upsert: true
          }
        }));
        await db.collection(config.collections.users.name)
          .bulkWrite(ops, { ordered: false });
      }
    });
  } finally {
    await session.endSession();
  }
}

async function ingestData(dataDir) {
  try {
    console.log('Iniciando ingesta de datos...');
    
    const client = await MongoClient.connect(
      `mongodb://${config.connection.host}:${config.connection.port}`,
      config.connection.options
    );
    
    const db = client.db(config.connection.database);
    
    // Obtener lista de archivos CSV
    const files = fs.readdirSync(dataDir)
      .filter(file => file.endsWith('_UkraineCombinedTweetsDeduped.csv'))
      .map(file => path.join(dataDir, file));
    
    console.log(`Encontrados ${files.length} archivos CSV para procesar`);
    
    // Procesar archivos secuencialmente para evitar sobrecarga de memoria
    for (const file of files) {
      console.log(`Procesando archivo: ${path.basename(file)}`);
      await processCsvFile(file, db);
    }
    
    console.log('Ingesta de datos completada');
    await client.close();
    
  } catch (error) {
    console.error('Error durante la ingesta de datos:', error);
    process.exit(1);
  }
}

// Ejecutar la ingesta de datos
const dataDir = path.join(__dirname, '../../dataset_ukraine');
ingestData(dataDir).catch(console.error);