const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');
const { MongoClient } = require('mongodb');
const config = require('../config/mongodb.config');
const os = require('os');

// Configuración optimizada para Ryzen 7 4700U (8 cores, 16 threads)
const BATCH_SIZE = 250; // Reducido para menor uso de memoria
const PAUSE_BETWEEN_BATCHES = 500; // ms
const MAX_MEMORY_PERCENT = 70; // Límite de uso de memoria
const CPU_THROTTLE = 0.7; // Usar 70% de CPU máximo

// Función de pausa para throttling
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// Monitorear uso de recursos
function checkResources() {
    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memoryUsage = ((totalMem - freeMem) / totalMem) * 100;
    const cpuUsage = os.loadavg()[0] / os.cpus().length * 100;

    return {
        memoryUsage,
        cpuUsage,
        shouldThrottle: memoryUsage > MAX_MEMORY_PERCENT || cpuUsage > CPU_THROTTLE * 100
    };
}

// Función auxiliar para parsear JSON con comillas simples
function parseJsonWithSingleQuotes(str) {
    if (!str || str === "") return null;
    try {
        const jsonStr = str.replace(/'/g, '"');
        return JSON.parse(jsonStr);
    } catch (error) {
        return null;
    }
}

// Función para limpiar la memoria
async function gcCollect() {
    if (global.gc) {
        global.gc();
    }
    await sleep(100); // Dar tiempo al GC
}

// Función para procesar y transformar un tweet
function processTweet(rawTweet) {
    let hashtags = [];
    try {
        const parsedHashtags = parseJsonWithSingleQuotes(rawTweet.hashtags);
        if (parsedHashtags) {
            hashtags = parsedHashtags.map(h => h.text);
        }
    } catch (error) {
        // Silenciosamente continuar con array vacío de hashtags
    }

    let coordinates = null;
    if (rawTweet.coordinates && rawTweet.coordinates !== "") {
        try {
            const parsedCoords = parseJsonWithSingleQuotes(rawTweet.coordinates);
            if (parsedCoords && parsedCoords.type === 'Point') {
                coordinates = {
                    type: 'Point',
                    coordinates: parsedCoords.coordinates
                };
            }
        } catch (error) {
            // Silenciosamente continuar sin coordenadas
        }
    }

    return {
        _id: rawTweet.tweetid,
        userid: rawTweet.userid,
        username: rawTweet.username,
        tweetcreatedts: new Date(rawTweet.tweetcreatedts),
        retweetcount: parseInt(rawTweet.retweetcount, 10) || 0,
        text: rawTweet.text,
        hashtags: hashtags,
        language: rawTweet.language || 'unknown',
        coordinates: coordinates,
        favorite_count: parseInt(rawTweet.favorite_count, 10) || 0,
        is_retweet: rawTweet.is_retweet === 'true',
        original_tweet_id: rawTweet.original_tweet_id || null,
        original_tweet_userid: rawTweet.original_tweet_userid || null,
        original_tweet_username: rawTweet.original_tweet_username || null,
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
        following: parseInt(rawTweet.following, 10) || 0,
        followers: parseInt(rawTweet.followers, 10) || 0,
        totaltweets: parseInt(rawTweet.totaltweets, 10) || 0,
        usercreatedts: new Date(rawTweet.usercreatedts)
    };
}

// Función para verificar si un archivo ya fue procesado
async function isFileProcessed(db, filename) {
    const checkpoint = await db.collection('ingestion_checkpoint').findOne({ filename });
    return checkpoint !== null;
}

// Función para marcar un archivo como procesado
async function markFileAsProcessed(db, filename, stats) {
    await db.collection('ingestion_checkpoint').insertOne({
        filename,
        processedAt: new Date(),
        stats: stats
    });
}

async function processCsvFile(filePath, db) {
    const tweets = [];
    const users = new Map();
    let tweetCount = 0;
    let userCount = 0;
    let successfulTweets = 0;
    let errorCount = 0;
    let stream = null;

    return new Promise((resolve, reject) => {
        const cleanup = async () => {
            if (stream) {
                stream.destroy();
            }
            tweets.length = 0;
            users.clear();
            await gcCollect();
        };

        try {
            stream = fs.createReadStream(filePath, { highWaterMark: 64 * 1024 }) // 64KB chunks
                .pipe(csv())
                .on('data', async (row) => {
                    try {
                        // Verificar recursos y throttle si es necesario
                        const resources = checkResources();
                        if (resources.shouldThrottle) {
                            stream.pause();
                            await sleep(PAUSE_BETWEEN_BATCHES);
                            stream.resume();
                        }

                        const tweet = processTweet(row);
                        tweets.push(tweet);
                        tweetCount++;

                        if (!users.has(row.userid)) {
                            users.set(row.userid, processUser(row));
                            userCount++;
                        }

                        if (tweets.length >= BATCH_SIZE) {
                            stream.pause();
                            try {
                                const batchStats = await insertBatch(db, tweets, Array.from(users.values()));
                                successfulTweets += batchStats.insertedTweets;
                                tweets.length = 0;
                                users.clear();
                                await gcCollect();
                            } catch (error) {
                                console.error(`Error insertando lote: ${error}`);
                                errorCount++;
                            }
                            stream.resume();
                            await sleep(PAUSE_BETWEEN_BATCHES);
                        }
                    } catch (error) {
                        console.error(`Error procesando fila: ${error}`);
                        errorCount++;
                    }
                })
                .on('end', async () => {
                    try {
                        if (tweets.length > 0) {
                            const finalBatchStats = await insertBatch(db, tweets, Array.from(users.values()));
                            successfulTweets += finalBatchStats.insertedTweets;
                        }

                        const stats = {
                            totalTweets: tweetCount,
                            successfulTweets: successfulTweets,
                            users: userCount,
                            errors: errorCount,
                            completedAt: new Date()
                        };

                        await markFileAsProcessed(db, path.basename(filePath), stats);
                        await cleanup();
                        
                        console.log(`Archivo ${path.basename(filePath)} procesado:`, {
                            ...stats,
                            errorRate: `${((errorCount / tweetCount) * 100).toFixed(2)}%`
                        });
                        resolve(stats);
                    } catch (error) {
                        await cleanup();
                        reject(error);
                    }
                })
                .on('error', async (error) => {
                    await cleanup();
                    reject(error);
                });
        } catch (error) {
            cleanup();
            reject(error);
        }
    });
}

async function insertBatch(db, tweets, users) {
    const session = db.client.startSession();
    let insertedTweets = 0;
    
    try {
        await session.withTransaction(async () => {
            if (tweets.length > 0) {
                const tweetOps = tweets.map(tweet => ({
                    updateOne: {
                        filter: { _id: tweet._id },
                        update: { $set: tweet },
                        upsert: true
                    }
                }));

                const tweetResult = await db.collection(config.collections.tweets.name)
                    .bulkWrite(tweetOps, { 
                        ordered: false,
                        wtimeout: 30000 // 30 segundos timeout
                    });
                
                insertedTweets = tweetResult.upsertedCount + tweetResult.modifiedCount;
            }

            if (users.length > 0) {
                const userOps = users.map(user => ({
                    updateOne: {
                        filter: { _id: user._id },
                        update: { $set: user },
                        upsert: true
                    }
                }));
                await db.collection(config.collections.users.name)
                    .bulkWrite(userOps, { 
                        ordered: false,
                        wtimeout: 30000
                    });
            }
        });

        return { insertedTweets };
    } finally {
        await session.endSession();
    }
}

async function ingestDataLocal() {
    let client = null;
    try {
        console.log('Iniciando ingesta de datos en MongoDB local...');
        console.log('Configuración del sistema:');
        console.log(`CPU: ${os.cpus().length} cores`);
        console.log(`Memoria total: ${Math.round(os.totalmem() / (1024 * 1024 * 1024))}GB`);
        console.log(`Batch size: ${BATCH_SIZE}`);
        console.log(`Pausa entre lotes: ${PAUSE_BETWEEN_BATCHES}ms`);
        console.log(`Límite de memoria: ${MAX_MEMORY_PERCENT}%`);
        console.log(`Throttle CPU: ${CPU_THROTTLE * 100}%`);
        
        client = await MongoClient.connect(
            `mongodb://${config.connection.host}:27017`,
            {
                ...config.connection.options,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000
            }
        );
        
        const db = client.db(config.connection.database);
        
        const dataDir = path.join(__dirname, '../../dataset_ukraine');
        const files = fs.readdirSync(dataDir)
            .filter(file => file.endsWith('_UkraineCombinedTweetsDeduped.csv'))
            .sort()
            .map(file => path.join(dataDir, file));
        
        console.log(`\nEncontrados ${files.length} archivos CSV`);
        
        let processedFiles = 0;
        let skippedFiles = 0;
        let totalTweets = 0;
        let successfulTweets = 0;
        let totalUsers = 0;
        let totalErrors = 0;

        for (const file of files) {
            const filename = path.basename(file);
            
            if (await isFileProcessed(db, filename)) {
                console.log(`Saltando archivo ya procesado: ${filename}`);
                skippedFiles++;
                continue;
            }

            console.log(`\nProcesando archivo (${processedFiles + 1}/${files.length}): ${filename}`);
            
            try {
                const stats = await processCsvFile(file, db);
                processedFiles++;
                totalTweets += stats.totalTweets;
                successfulTweets += stats.successfulTweets;
                totalUsers += stats.users;
                totalErrors += stats.errors;

                // Mostrar estado de recursos
                const resources = checkResources();
                console.log(`\nEstado del sistema:`);
                console.log(`- Uso de memoria: ${resources.memoryUsage.toFixed(1)}%`);
                console.log(`- Uso de CPU: ${resources.cpuUsage.toFixed(1)}%`);
                console.log(`\nProgreso: ${processedFiles + skippedFiles}/${files.length} archivos (${skippedFiles} saltados)`);
                console.log(`Acumulado: ${totalTweets} tweets totales, ${successfulTweets} insertados/actualizados, ${totalUsers} usuarios únicos, ${totalErrors} errores\n`);

                // Pausa entre archivos para permitir que el sistema se recupere
                await sleep(PAUSE_BETWEEN_BATCHES * 2);
            } catch (error) {
                console.error(`Error procesando archivo ${filename}:`, error);
                totalErrors++;
                // Pausa más larga después de un error
                await sleep(PAUSE_BETWEEN_BATCHES * 4);
            }
        }
        
        console.log('\nResumen de ingesta:');
        console.log(`- Total archivos: ${files.length}`);
        console.log(`- Archivos procesados: ${processedFiles}`);
        console.log(`- Archivos saltados: ${skippedFiles}`);
        console.log(`- Total tweets procesados: ${totalTweets}`);
        console.log(`- Tweets insertados/actualizados: ${successfulTweets}`);
        console.log(`- Total usuarios únicos: ${totalUsers}`);
        console.log(`- Total errores: ${totalErrors}`);
        console.log(`- Tasa de error: ${((totalErrors / totalTweets) * 100).toFixed(2)}%`);
        
    } catch (error) {
        console.error('Error durante la ingesta de datos:', error);
        process.exit(1);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

// Ejecutar la ingesta de datos si se ejecuta directamente
if (require.main === module) {
    // Configurar manejo de señales para limpieza
    process.on('SIGINT', async () => {
        console.log('\nDetectada señal de interrupción, limpiando...');
        if (global.gc) {
            global.gc();
        }
        process.exit(0);
    });

    // Habilitar recolección de basura manual si está disponible
    if (global.gc) {
        console.log('Recolección de basura manual habilitada');
    }
    
    ingestDataLocal().catch(console.error);
}

module.exports = ingestDataLocal;
