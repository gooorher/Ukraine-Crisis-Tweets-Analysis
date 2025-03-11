// Script para inicializar el cluster de MongoDB
const { MongoClient } = require('mongodb');

async function initializeConfigServer() {
  try {
    console.log('Iniciando configuración del Config Server Replica Set...');
    const configClient = await MongoClient.connect('mongodb://localhost:27017');
    const configAdmin = configClient.db('admin');

    // Inicializar replica set de config servers
    const cfgrsConfig = {
      _id: "cfgrs",
      configsvr: true,
      members: [
        { _id: 0, host: "cfgsvr1:27017" },
        { _id: 1, host: "cfgsvr2:27017" },
        { _id: 2, host: "cfgsvr3:27017" }
      ]
    };

    await configAdmin.command({ replSetInitiate: cfgrsConfig });
    console.log('Config Server Replica Set iniciado');
    await configClient.close();
  } catch (error) {
    console.error('Error inicializando Config Server:', error);
    throw error;
  }
}

async function initializeShard(shardName, port) {
  try {
    console.log(`Iniciando configuración del Shard ${shardName}...`);
    const shardClient = await MongoClient.connect(`mongodb://localhost:${port}`);
    const shardAdmin = shardClient.db('admin');

    // Inicializar replica set del shard
    const shardConfig = {
      _id: `${shardName}rs`,
      members: [
        { _id: 0, host: `${shardName}svr1:27017` },
        { _id: 1, host: `${shardName}svr2:27017` },
        { _id: 2, host: `${shardName}svr3:27017` }
      ]
    };

    await shardAdmin.command({ replSetInitiate: shardConfig });
    console.log(`Shard ${shardName} Replica Set iniciado`);
    await shardClient.close();
  } catch (error) {
    console.error(`Error inicializando Shard ${shardName}:`, error);
    throw error;
  }
}

async function addShardsToCluster() {
  try {
    console.log('Añadiendo shards al cluster...');
    // Conectar al mongos router
    const mongosClient = await MongoClient.connect('mongodb://localhost:27029');
    const mongosAdmin = mongosClient.db('admin');

    // Añadir cada shard
    await mongosAdmin.command({
      addShard: "shard1rs/shard1svr1:27017,shard1svr2:27017,shard1svr3:27017"
    });
    await mongosAdmin.command({
      addShard: "shard2rs/shard2svr1:27017,shard2svr2:27017,shard2svr3:27017"
    });
    await mongosAdmin.command({
      addShard: "shard3rs/shard3svr1:27017,shard3svr2:27017,shard3svr3:27017"
    });

    console.log('Shards añadidos exitosamente');
    await mongosClient.close();
  } catch (error) {
    console.error('Error añadiendo shards:', error);
    throw error;
  }
}

async function enableSharding() {
  try {
    console.log('Habilitando sharding para la base de datos y colecciones...');
    const mongosClient = await MongoClient.connect('mongodb://localhost:27029');
    const mongosAdmin = mongosClient.db('admin');

    // Habilitar sharding para la base de datos
    await mongosAdmin.command({ enableSharding: 'ukraine_crisis' });

    // Habilitar sharding para las colecciones
    const db = mongosClient.db('ukraine_crisis');
    
    // Crear índice para la clave de sharding de tweets
    await db.collection('tweets').createIndex({ tweetcreatedts: 1 });
    
    // Habilitar sharding para tweets usando tweetcreatedts
    await mongosAdmin.command({
      shardCollection: 'ukraine_crisis.tweets',
      key: { tweetcreatedts: 1 }
    });

    // Crear índice para la clave de sharding de users
    await db.collection('users').createIndex({ userid: 'hashed' });
    
    // Habilitar sharding para users usando userid
    await mongosAdmin.command({
      shardCollection: 'ukraine_crisis.users',
      key: { userid: 'hashed' }
    });

    console.log('Sharding habilitado exitosamente');
    await mongosClient.close();
  } catch (error) {
    console.error('Error habilitando sharding:', error);
    throw error;
  }
}

async function initializeCluster() {
  try {
    console.log('Iniciando configuración del cluster MongoDB...');

    // Esperar un poco para asegurar que todos los servicios estén listos
    await new Promise(resolve => setTimeout(resolve, 30000));

    // Inicializar config servers
    await initializeConfigServer();

    // Inicializar shards
    await initializeShard('shard1', 27020);
    await initializeShard('shard2', 27023);
    await initializeShard('shard3', 27026);

    // Esperar a que los replica sets se estabilicen
    await new Promise(resolve => setTimeout(resolve, 30000));

    // Añadir shards al cluster
    await addShardsToCluster();

    // Habilitar sharding
    await enableSharding();

    console.log('Cluster MongoDB configurado exitosamente');
  } catch (error) {
    console.error('Error durante la configuración del cluster:', error);
    process.exit(1);
  }
}

// Ejecutar la inicialización
initializeCluster().catch(console.error);