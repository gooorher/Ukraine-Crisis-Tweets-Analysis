from pymongo import MongoClient
from datetime import datetime
import sys

def test_mongodb_connection():
    try:
        # Conectar a MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['ukraine_crisis']
        
        # Intentar una operación simple
        result = db.tweets.find_one()
        
        if result:
            print("✅ Conexión exitosa a MongoDB")
            print(f"✅ Base de datos 'ukraine_crisis' encontrada")
            print(f"✅ Colección 'tweets' encontrada")
            print(f"✅ Ejemplo de documento encontrado con ID: {result.get('_id')}")
            print(f"✅ Fecha del tweet: {result.get('tweetcreatedts')}")
            return True
        else:
            print("❌ No se encontraron documentos en la colección 'tweets'")
            return False
            
    except Exception as e:
        print(f"❌ Error al conectar a MongoDB: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nProbando conexión a MongoDB...\n")
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)