import unittest
from app import app
from datetime import datetime, timedelta
import json

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_trends_page(self):
        """Prueba la página principal de tendencias"""
        response = self.app.get('/trends/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ukraine Crisis Twitter Analysis', response.data)

    def test_trends_api_data(self):
        """Prueba el endpoint de datos de tendencias"""
        response = self.app.get('/trends/api/data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('success' in data)
        self.assertTrue('data' in data)

    def test_tweet_volume_api(self):
        """Prueba el endpoint de volumen de tweets"""
        response = self.app.get('/trends/api/volume')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('success' in data)
        self.assertTrue('data' in data)

    def test_engagement_api(self):
        """Prueba el endpoint de métricas de engagement"""
        response = self.app.get('/trends/api/engagement')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('success' in data)
        self.assertTrue('data' in data)

    def test_hourly_distribution_api(self):
        """Prueba el endpoint de distribución horaria"""
        response = self.app.get('/trends/api/hourly')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('success' in data)
        self.assertTrue('data' in data)

    def test_date_range_filter(self):
        """Prueba el filtrado por rango de fechas"""
        ranges = ['7d', '30d', '90d', 'all']
        for range_str in ranges:
            response = self.app.get(f'/trends/api/data?range={range_str}')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue('success' in data)
            self.assertTrue('data' in data)

    def test_exports(self):
        """Prueba los endpoints de exportación"""
        formats = ['csv', 'json']
        for fmt in formats:
            response = self.app.get(f'/trends/export/{fmt}')
            self.assertEqual(response.status_code, 200)

    def test_error_handling(self):
        """Prueba el manejo de errores"""
        # Prueba 404
        response = self.app.get('/ruta-no-existente')
        self.assertEqual(response.status_code, 404)

        # Prueba parámetro inválido
        response = self.app.get('/trends/api/data?range=invalid')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()