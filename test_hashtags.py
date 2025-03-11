import unittest
from datetime import datetime, timedelta
from flask_app import create_app
from flask_app.utils.date_utils import parse_date_range
import json

class TestHashtags(unittest.TestCase):
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.base_date = datetime.now()
    
    def test_hashtags_page_loads(self):
        """Verifica que la página de hashtags cargue correctamente"""
        response = self.client.get('/hashtags/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'hashtags.hashtags_page', response.data)
    
    def test_frequency_api(self):
        """Verifica el endpoint de frecuencia de hashtags"""
        # Probar diferentes rangos de fecha
        ranges = ['7d', '30d', '90d', 'all']
        
        for range_type in ranges:
            response = self.client.get(f'/hashtags/api/frequency?range={range_type}&limit=20')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIsInstance(data['data'], list)
            
            if data['data']:  # Si hay datos
                first_hashtag = data['data'][0]
                self.assertIn('hashtag', first_hashtag)
                self.assertIn('count', first_hashtag)
                self.assertIn('engagement', first_hashtag)
                self.assertIn('avg_engagement', first_hashtag)
    
    def test_popularity_api(self):
        """Verifica el endpoint de evolución temporal de hashtags"""
        # Probar sin hashtags específicos (debería usar los más frecuentes)
        response = self.client.get('/hashtags/api/popularity?range=30d')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], dict)
        
        # Probar con hashtags específicos
        test_hashtags = ['Ukraine', 'Russia']
        response = self.client.get(
            '/hashtags/api/popularity?range=30d&' + '&'.join(f'hashtags[]={h}' for h in test_hashtags)
        )
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        if data['data']:  # Si hay datos
            # Verificar formato de los datos
            for hashtag, series in data['data'].items():
                self.assertIsInstance(series, list)
                if series:  # Si la serie tiene puntos
                    point = series[0]
                    self.assertIn('date', point)
                    self.assertIn('count', point)
                    self.assertIn('engagement', point)
    
    def test_cooccurrence_api(self):
        """Verifica el endpoint de co-ocurrencia de hashtags"""
        response = self.client.get('/hashtags/api/cooccurrence?range=30d')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('nodes', data['data'])
        self.assertIn('links', data['data'])
        
        # Verificar estructura de nodos y enlaces
        if data['data']['nodes']:  # Si hay nodos
            node = data['data']['nodes'][0]
            self.assertIn('id', node)
            self.assertIn('weight', node)
            
        if data['data']['links']:  # Si hay enlaces
            link = data['data']['links'][0]
            self.assertIn('source', link)
            self.assertIn('target', link)
            self.assertIn('value', link)
    
    def test_date_validation(self):
        """Verifica la validación de rangos de fecha"""
        # Probar rango de fechas inválido
        response = self.client.get('/hashtags/api/frequency?range=invalid')
        self.assertEqual(response.status_code, 200)  # Debería usar rango por defecto
        
        # Probar fechas específicas
        start_date = self.base_date - timedelta(days=30)
        end_date = self.base_date
        response = self.client.get(
            f'/hashtags/api/frequency?start_date={start_date.strftime("%Y-%m-%d")}&'
            f'end_date={end_date.strftime("%Y-%m-%d")}'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_data_consistency(self):
        """Verifica la consistencia de los datos entre endpoints"""
        # Obtener hashtags más frecuentes
        freq_response = self.client.get('/hashtags/api/frequency?range=30d&limit=5')
        freq_data = json.loads(freq_response.data)
        
        if freq_data['data']:  # Si hay datos de frecuencia
            # Verificar que estos hashtags aparezcan en los datos de popularidad
            hashtags = [h['hashtag'] for h in freq_data['data']]
            pop_response = self.client.get(
                '/hashtags/api/popularity?range=30d&' + '&'.join(f'hashtags[]={h}' for h in hashtags)
            )
            pop_data = json.loads(pop_response.data)
            
            # Verificar que todos los hashtags frecuentes tienen datos de popularidad
            for hashtag in hashtags:
                self.assertIn(hashtag, pop_data['data'])
    
    def test_error_handling(self):
        """Verifica el manejo de errores"""
        # Probar límite inválido
        response = self.client.get('/hashtags/api/frequency?range=30d&limit=invalid')
        self.assertEqual(response.status_code, 500)
        
        # Probar rango de fechas muy grande
        response = self.client.get('/hashtags/api/frequency?range=999d')
        self.assertEqual(response.status_code, 200)  # Debería usar rango por defecto
        
        # Probar hashtags vacíos
        response = self.client.get('/hashtags/api/popularity?range=30d&hashtags[]=')
        self.assertEqual(response.status_code, 200)  # Debería ignorar hashtags vacíos

if __name__ == '__main__':
    unittest.main()