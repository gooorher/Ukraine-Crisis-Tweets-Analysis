import unittest
from datetime import datetime, timedelta
from flask_app import create_app
from flask_app.utils.date_utils import parse_date_range
import json

class TestUsers(unittest.TestCase):
    def setUp(self):
        """Configuracion inicial para cada prueba"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.base_date = datetime.now()
    
    def test_users_page_loads(self):
        """Verifica que la pagina de usuarios cargue correctamente"""
        response = self.client.get('/users/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Analisis de Usuarios', response.data)
    
    def test_activity_api(self):
        """Verifica el endpoint de actividad de usuarios"""
        # Probar diferentes rangos de fecha
        ranges = ['7d', '30d', '90d', 'all']
        
        for range_type in ranges:
            response = self.client.get(f'/users/api/activity?range={range_type}&limit=20')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIsInstance(data['data'], list)
            
            if data['data']:  # Si hay datos
                first_user = data['data'][0]
                self.assertIn('username', first_user)
                self.assertIn('tweet_count', first_user)
                self.assertIn('engagement', first_user)
                self.assertIn('followers', first_user)
    
    def test_engagement_api(self):
        """Verifica el endpoint de engagement de usuarios"""
        response = self.client.get('/users/api/engagement?range=30d&limit=20')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
        
        if data['data']:  # Si hay datos
            first_user = data['data'][0]
            self.assertIn('username', first_user)
            self.assertIn('engagement_rate', first_user)
            self.assertIn('tweet_count', first_user)
            self.assertGreaterEqual(first_user['engagement_rate'], 0)
    
    def test_influence_api(self):
        """Verifica el endpoint de influencia de usuarios y sus cálculos"""
        # Probar endpoint básico
        response = self.client.get('/users/api/influence?range=30d&limit=20')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
        
        if data['data']:  # Si hay datos
            first_user = data['data'][0]
            required_fields = ['username', 'influence_score', 'followers',
                             'engagement_rate', 'tweet_count', 'verified']
            
            # Verificar campos requeridos
            for field in required_fields:
                self.assertIn(field, first_user)
            
            # Verificar restricciones de valores
            self.assertGreaterEqual(first_user['influence_score'], 0)
            self.assertLessEqual(first_user['influence_score'], 100)
            self.assertGreaterEqual(first_user['engagement_rate'], 0)
            self.assertIsInstance(first_user['verified'], bool)
            
            # Verificar ordenamiento por influence_score
            if len(data['data']) > 1:
                self.assertGreaterEqual(
                    first_user['influence_score'],
                    data['data'][1]['influence_score']
                )
    
    def test_influence_edge_cases(self):
        """Prueba casos extremos en el cálculo de influencia"""
        # Probar diferentes límites
        for limit in [5, 20, 50]:
            response = self.client.get(f'/users/api/influence?range=30d&limit={limit}')
            data = json.loads(response.data)
            if data['success'] and data['data']:
                self.assertLessEqual(len(data['data']), limit)
        
        # Probar rango de fechas vacío
        response = self.client.get('/users/api/influence?range=1d')
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Probar límite inválido
        response = self.client.get('/users/api/influence?range=30d&limit=invalid')
        self.assertEqual(response.status_code, 500)
        
        # Probar rango de fechas muy grande
        response = self.client.get('/users/api/influence?range=999d')
        self.assertEqual(response.status_code, 200)
    
    def test_influence_calculation_consistency(self):
        """Verifica la consistencia en el cálculo de influence_score"""
        response = self.client.get('/users/api/influence?range=30d&limit=10')
        data = json.loads(response.data)
        
        if data['success'] and len(data['data']) >= 2:
            user1 = data['data'][0]
            user2 = data['data'][1]
            
            # Usuario con más engagement y followers debería tener mayor score
            if (user1['engagement_rate'] > user2['engagement_rate'] and
                user1['followers'] > user2['followers']):
                self.assertGreater(user1['influence_score'], user2['influence_score'])
            
            # Verificar que el score refleje tanto engagement como followers
            for user in data['data']:
                self.assertGreaterEqual(user['influence_score'], 0)
                self.assertLessEqual(user['influence_score'], 100)
                
                # Si no hay tweets o followers, el score debería ser bajo
                if user['tweet_count'] == 0 or user['followers'] == 0:
                    self.assertLess(user['influence_score'], 50)
    
    def test_user_details_api(self):
        """Verifica el endpoint de detalles de usuario"""
        # Primero obtener un usuario valido
        response = self.client.get('/users/api/activity?range=30d&limit=1')
        data = json.loads(response.data)
        
        if data['data']:  # Si hay datos
            username = data['data'][0]['username']
            response = self.client.get(f'/users/api/user/{username}?range=30d')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('username', data['data'])
            self.assertIn('tweet_count', data['data'])
            self.assertIn('recent_tweets', data['data'])
    
    def test_evolution_api(self):
        """Verifica el endpoint de evolucion de usuarios"""
        # Primero obtener usuarios validos
        response = self.client.get('/users/api/activity?range=30d&limit=3')
        users_data = json.loads(response.data)
        
        if users_data['data']:  # Si hay datos
            usernames = [user['username'] for user in users_data['data']]
            response = self.client.get(
                '/users/api/evolution?range=30d&' + '&'.join(f'users[]={u}' for u in usernames)
            )
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verificar estructura de datos para cada usuario
            for username in usernames:
                self.assertIn(username, data['data'])
                user_data = data['data'][username]
                self.assertIsInstance(user_data, list)
                
                if user_data:  # Si hay puntos de datos
                    point = user_data[0]
                    self.assertIn('date', point)
                    self.assertIn('tweet_count', point)
                    self.assertIn('engagement', point)
    
    def test_error_handling(self):
        """Verifica el manejo de errores"""
        # Probar limite invalido
        response = self.client.get('/users/api/activity?range=30d&limit=invalid')
        self.assertEqual(response.status_code, 500)
        
        # Probar rango de fechas muy grande
        response = self.client.get('/users/api/activity?range=999d')
        self.assertEqual(response.status_code, 200)  # Deberia usar rango por defecto
        
        # Probar usuario inexistente
        response = self.client.get('/users/api/user/nonexistentuser')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIsNone(data['data'])
    
    def test_data_consistency(self):
        """Verifica la consistencia de los datos entre endpoints"""
        # Obtener usuarios mas activos
        response = self.client.get('/users/api/activity?range=30d&limit=5')
        activity_data = json.loads(response.data)
        
        if activity_data['data']:  # Si hay datos de actividad
            username = activity_data['data'][0]['username']
            
            # Verificar que el usuario aparezca en los datos de engagement
            response = self.client.get('/users/api/engagement?range=30d')
            engagement_data = json.loads(response.data)
            
            engagement_usernames = [u['username'] for u in engagement_data['data']]
            self.assertIn(username, engagement_usernames)
            
            # Verificar que los detalles del usuario coincidan
            response = self.client.get(f'/users/api/user/{username}?range=30d')
            user_data = json.loads(response.data)
            
            self.assertEqual(
                activity_data['data'][0]['tweet_count'],
                user_data['data']['tweet_count']
            )

if __name__ == '__main__':
    unittest.main()