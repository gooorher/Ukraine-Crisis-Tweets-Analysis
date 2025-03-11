/**
 * Configuración de MongoDB local para el análisis de datos de Twitter sobre la crisis de Ucrania
 */
const { MongoClient } = require('mongodb');
const config = require('../config/mongodb.config');

async function setupMongoLocal() {
    try {
        console.log('Iniciando configuración de MongoDB local...');
        
        // Conectar al servidor MongoDB local
        const client = await MongoClient.connect(
            `mongodb://${config.connection.host}:27017`,
            config.connection.options
        );
        
        console.log('Conexión establecida con MongoDB');
        
        // Obtener referencia a la base de datos
        const db = client.db(config.connection.database);
        
        // Eliminar colecciones existentes si existen
        const collections = await db.listCollections().toArray();
        for (const collection of collections) {
            if (collection.name !== 'ingestion_checkpoint') {
                await db.collection(collection.name).drop();
                console.log(`Colección ${collection.name} eliminada`);
            }
        }

        // Crear colecciones con la nueva configuración
        for (const [collectionName, collectionConfig] of Object.entries(config.collections)) {
            console.log(`Configurando colección ${collectionConfig.name}...`);

            // Crear colección
            await db.createCollection(collectionConfig.name);
            console.log(`Colección ${collectionConfig.name} creada`);

            // Crear índices
            for (const index of collectionConfig.indexes) {
                const options = {
                    background: true,
                    name: Object.keys(index.key).join('_'),
                    ...index.options
                };

                await db.collection(collectionConfig.name).createIndex(index.key, options);
                console.log(`Índice ${options.name} creado para ${collectionConfig.name}`);
            }
        }

        // Configurar checkpoint collection si no existe
        if (!(await db.listCollections({ name: 'ingestion_checkpoint' }).hasNext())) {
            await db.createCollection('ingestion_checkpoint');
            await db.collection('ingestion_checkpoint').createIndex(
                { filename: 1 },
                { unique: true }
            );
            console.log('Colección ingestion_checkpoint configurada');
        }

        console.log('Configuración de MongoDB local completada con éxito');
        await client.close();
        
    } catch (error) {
        console.error('Error durante la configuración de MongoDB local:', error);
        process.exit(1);
    }
}

// Ejecutar la configuración
if (require.main === module) {
    setupMongoLocal().catch(console.error);
}

module.exports = setupMongoLocal;