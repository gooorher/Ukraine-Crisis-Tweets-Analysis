const { MongoClient } = require('mongodb');
const config = require('../config/mongodb.config');

async function setupMongoDB() {
  try {
    console.log('Iniciando configuración de MongoDB...');
    
    // Conectar al servidor MongoDB
    const client = await MongoClient.connect(
      `mongodb://${config.connection.host}:${config.connection.port}`,
      config.connection.options
    );
    
    console.log('Conexión establecida con MongoDB');
    
    // Obtener referencia a la base de datos
    const db = client.db(config.connection.database);
    
    // Habilitar sharding en la base de datos
    if (config.cluster.shardingEnabled) {
      await client.db('admin').command({ enableSharding: config.connection.database });
      console.log(`Sharding habilitado para la base de datos ${config.connection.database}`);
    }

    // Configurar colecciones
    for (const [collectionName, collectionConfig] of Object.entries(config.collections)) {
      // Crear colección si no existe
      if (!(await db.listCollections({ name: collectionConfig.name }).hasNext())) {
        await db.createCollection(collectionConfig.name);
        console.log(`Colección ${collectionConfig.name} creada`);
      }

      // Habilitar sharding para la colección
      if (config.cluster.shardingEnabled) {
        await client.db('admin').command({
          shardCollection: `${config.connection.database}.${collectionConfig.name}`,
          key: collectionConfig.shardKey
        });
        console.log(`Sharding habilitado para la colección ${collectionConfig.name}`);

        // Pre-split chunks si es necesario
        if (collectionName === 'tweets' && config.sharding.presplitRanges[collectionName]) {
          const ranges = config.sharding.presplitRanges[collectionName].ranges;
          for (const range of ranges) {
            await client.db('admin').command({
              split: `${config.connection.database}.${collectionConfig.name}`,
              middle: { tweetcreatedts: range.min }
            });
          }
          console.log(`Chunks pre-split realizados para la colección ${collectionConfig.name}`);
        }
      }

      // Crear índices
      for (const index of collectionConfig.indexes) {
        await db.collection(collectionConfig.name).createIndex(index.key, {
          background: true,
          name: Object.keys(index.key).join('_')
        });
      }
      console.log(`Índices creados para la colección ${collectionConfig.name}`);
    }

    console.log('Configuración de MongoDB completada con éxito');
    await client.close();
    
  } catch (error) {
    console.error('Error durante la configuración de MongoDB:', error);
    process.exit(1);
  }
}

// Ejecutar la configuración
setupMongoDB().catch(console.error);