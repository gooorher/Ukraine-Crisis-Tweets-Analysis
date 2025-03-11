import unittest
from flask_app import create_app
from flask_app.logging_config import setup_logging, log_to_file, log_to_db, MongoDBHandler
import logging
import os
from datetime import datetime
import json
import tempfile
import shutil

class TestLogging(unittest.TestCase):
    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Crear directorio temporal para logs
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Configurar aplicación de prueba
        self.app = create_app({
            'TESTING': True,
            'DEBUG': False,
            'MONGO_URI': 'mongodb://localhost:27017/test_db'
        })
        
        # Configurar logging para pruebas
        self.log_file = os.path.join(self.test_dir, 'test.log')
        self.handler = logging.FileHandler(self.log_file)
        self.handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        self.app.logger.addHandler(self.handler)
        self.app.logger.setLevel(logging.DEBUG)
        
        # Cliente de prueba
        self.client = self.app.test_client()
    
    def test_log_file_creation(self):
        """Verifica que se creen los archivos de log"""
        setup_logging(self.app)
        
        # Verificar que exista el directorio de logs
        self.assertTrue(os.path.exists('logs'))
        
        # Verificar que existan los archivos de log
        self.assertTrue(os.path.exists('logs/flask_app.log'))
        self.assertTrue(os.path.exists('logs/errors.log'))
        self.assertTrue(os.path.exists('logs/access.log'))
    
    def test_log_levels(self):
        """Verifica que los niveles de log funcionen correctamente"""
        with self.app.app_context():
            # Log de debug
            log_to_file('Test debug message', level=logging.DEBUG)
            
            # Log de info
            log_to_file('Test info message', level=logging.INFO)
            
            # Log de error
            log_to_file('Test error message', level=logging.ERROR)
            
            # Leer archivo de log
            with open(self.log_file, 'r') as f:
                logs = f.readlines()
            
            # Verificar niveles
            self.assertTrue(any('DEBUG' in line for line in logs))
            self.assertTrue(any('INFO' in line for line in logs))
            self.assertTrue(any('ERROR' in line for line in logs))
    
    def test_request_logging(self):
        """Verifica que se registren los requests"""
        # Hacer una petición
        response = self.client.get('/')
        
        # Verificar log de acceso
        with open('logs/access.log', 'r') as f:
            access_log = f.read()
            self.assertIn('GET /', access_log)
            self.assertIn(str(response.status_code), access_log)
    
    def test_error_logging(self):
        """Verifica que se registren los errores"""
        # Provocar un error 404
        response = self.client.get('/ruta_inexistente')
        
        # Verificar log de errores
        with open('logs/errors.log', 'r') as f:
            error_log = f.read()
            self.assertIn('404', error_log)
            self.assertIn('/ruta_inexistente', error_log)
    
    def test_mongodb_logging(self):
        """Verifica que funcione el logging en MongoDB"""
        with self.app.app_context():
            # Crear handler de MongoDB
            mongo_handler = MongoDBHandler()
            self.app.logger.addHandler(mongo_handler)
            
            # Generar un log
            test_message = f'Test message {datetime.now().isoformat()}'
            log_to_db(test_message, extra={'test_key': 'test_value'})
            
            # Verificar en MongoDB
            log_entry = self.app.mongo.db.logs.find_one({'message': test_message})
            self.assertIsNotNone(log_entry)
            self.assertEqual(log_entry['data']['test_key'], 'test_value')
    
    def test_extra_data_logging(self):
        """Verifica que se guarden datos adicionales en los logs"""
        with self.app.app_context():
            # Log con datos extra
            extra_data = {
                'user_id': '123',
                'action': 'test',
                'timestamp': datetime.now().isoformat()
            }
            
            log_to_file('Test with extra data', extra=extra_data)
            
            # Verificar en archivo
            with open(self.log_file, 'r') as f:
                log_content = f.read()
                self.assertIn('user_id', log_content)
                self.assertIn('action', log_content)
    
    def test_error_email_config(self):
        """Verifica la configuración de emails para errores"""
        # Configurar email
        self.app.config.update({
            'MAIL_SERVER': 'smtp.test.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'test@test.com',
            'MAIL_PASSWORD': 'password',
            'ADMINS': ['admin@test.com']
        })
        
        setup_logging(self.app)
        
        # Verificar handler de email
        mail_handlers = [h for h in self.app.logger.handlers 
                        if isinstance(h, logging.handlers.SMTPHandler)]
        self.assertEqual(len(mail_handlers), 1)
        
        handler = mail_handlers[0]
        self.assertEqual(handler.mailhost, ('smtp.test.com', 587))
        self.assertEqual(handler.toaddrs, ['admin@test.com'])
    
    def test_log_rotation(self):
        """Verifica que la rotación de logs funcione"""
        # Configurar un archivo de log pequeño
        test_log = os.path.join(self.test_dir, 'rotating.log')
        handler = logging.handlers.RotatingFileHandler(
            test_log,
            maxBytes=1024,  # 1KB
            backupCount=3
        )
        self.app.logger.addHandler(handler)
        
        # Generar logs hasta que rote
        large_message = 'x' * 512  # 512 bytes
        for _ in range(10):  # Debería generar múltiples archivos
            self.app.logger.info(large_message)
        
        # Verificar archivos de backup
        self.assertTrue(os.path.exists(test_log))
        self.assertTrue(os.path.exists(test_log + '.1'))
        
    def test_json_logging(self):
        """Verifica el formato JSON para logs estructurados"""
        json_log = os.path.join(self.test_dir, 'json.log')
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                data = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module
                }
                if hasattr(record, 'extra'):
                    data.update(record.extra)
                return json.dumps(data)
        
        handler = logging.FileHandler(json_log)
        handler.setFormatter(JsonFormatter())
        self.app.logger.addHandler(handler)
        
        # Generar log
        extra_data = {'user_id': '123', 'action': 'test'}
        log_to_file('Test JSON log', extra=extra_data)
        
        # Verificar formato JSON
        with open(json_log, 'r') as f:
            log_entry = json.loads(f.readline())
            self.assertEqual(log_entry['message'], 'Test JSON log')
            self.assertEqual(log_entry['user_id'], '123')

if __name__ == '__main__':
    unittest.main()