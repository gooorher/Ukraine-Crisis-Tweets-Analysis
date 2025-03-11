#!/bin/bash

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
if [ ! -f ".env" ]; then
    echo "Creando archivo .env..."
    cat > .env << EOF
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
MONGO_URI=mongodb://localhost:27017/ukraine_crisis
SECRET_KEY=your-secret-key-here
EOF
fi

# Crear directorios necesarios
mkdir -p logs
mkdir -p reports

# Verificar instalación de MongoDB
if ! command -v mongod &> /dev/null; then
    echo "ADVERTENCIA: MongoDB no está instalado en el sistema"
    echo "Por favor, instala MongoDB siguiendo las instrucciones en:"
    echo "https://docs.mongodb.com/manual/installation/"
fi

# Verificar que MongoDB esté en ejecución
if ! pgrep -x "mongod" > /dev/null; then
    echo "ADVERTENCIA: MongoDB no está en ejecución"
    echo "Por favor, inicia MongoDB antes de ejecutar la aplicación"
fi

echo "Configuración completada."
echo "Para activar el entorno virtual ejecuta:"
echo "source venv/bin/activate"
echo ""
echo "Para ejecutar la aplicación:"
echo "python app.py"