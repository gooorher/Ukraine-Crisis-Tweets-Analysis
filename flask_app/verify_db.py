from pymongo import MongoClient
from config import Config
import sys

def verify_mongodb():
    """Verifica la conexión a MongoDB y la existencia de la base de datos"""
    try:
        # Intentar conectar a MongoDB
        print("Verificando conexión a MongoDB...")
        client = MongoClient(Config.MONGO_URI)
        
        # Verificar que el servidor está activo
        client.admin.command('ping')
        print("✅ Conexión a MongoDB establecida")
        
        # Obtener lista de bases de datos
        databases = client.list_database_names()
        print(f"\nBases de datos disponibles: {', '.join(databases)}")
        
        # Verificar si la base de datos ukraine_crisis existe
        if Config.MONGO_DB in databases:
            db = client[Config.MONGO_DB]
            print(f"\n✅ Base de datos '{Config.MONGO_DB}' encontrada")
            
            # Verificar colecciones
            collections = db.list_collection_names()
            print(f"Colecciones disponibles: {', '.join(collections)}")
            
            # Verificar documentos en cada colección
            for collection in collections:
                count = db[collection].count_documents({})
                print(f"- {collection}: {count:,} documentos")
                
            return True
        else:
            print(f"\n❌ Base de datos '{Config.MONGO_DB}' no encontrada")
            return False
            
    except Exception as e:
        print(f"\n❌ Error al conectar a MongoDB: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_mongodb()
    sys.exit(0 if success else 1)