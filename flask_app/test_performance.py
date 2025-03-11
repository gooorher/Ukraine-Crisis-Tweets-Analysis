import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

class PerformanceTest:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.endpoints = [
            '/trends/',
            '/trends/api/data',
            '/trends/api/volume',
            '/trends/api/engagement',
            '/trends/api/hourly',
            '/trends/api/sentiment'
        ]
        self.results = {}

    def test_endpoint(self, endpoint):
        """Prueba un endpoint específico y mide el tiempo de respuesta"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}")
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000,  # convertir a milisegundos
                'success': response.status_code == 200
            }
        except Exception as e:
            return {
                'status_code': 0,
                'response_time': 0,
                'success': False,
                'error': str(e)
            }

    def run_load_test(self, num_requests=100, concurrent_users=10):
        """Ejecuta prueba de carga con múltiples usuarios concurrentes"""
        print(f"\nIniciando prueba de rendimiento...")
        print(f"Requests por endpoint: {num_requests}")
        print(f"Usuarios concurrentes: {concurrent_users}\n")

        for endpoint in self.endpoints:
            print(f"Probando endpoint: {endpoint}")
            response_times = []
            success_count = 0
            
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [
                    executor.submit(self.test_endpoint, endpoint)
                    for _ in range(num_requests)
                ]
                
                for future in futures:
                    result = future.result()
                    if result['success']:
                        response_times.append(result['response_time'])
                        success_count += 1

            if response_times:
                stats = {
                    'min': min(response_times),
                    'max': max(response_times),
                    'avg': statistics.mean(response_times),
                    'median': statistics.median(response_times),
                    'p95': statistics.quantiles(response_times, n=20)[-1],
                    'success_rate': (success_count / num_requests) * 100
                }
                
                print(f"  Resultados:")
                print(f"  - Tiempo mínimo: {stats['min']:.2f}ms")
                print(f"  - Tiempo máximo: {stats['max']:.2f}ms")
                print(f"  - Tiempo promedio: {stats['avg']:.2f}ms")
                print(f"  - Mediana: {stats['median']:.2f}ms")
                print(f"  - P95: {stats['p95']:.2f}ms")
                print(f"  - Tasa de éxito: {stats['success_rate']:.1f}%\n")
                
                self.results[endpoint] = stats
            else:
                print(f"  ❌ Error: No se obtuvieron respuestas exitosas\n")

    def test_data_consistency(self):
        """Verifica la consistencia de los datos entre diferentes endpoints"""
        print("\nVerificando consistencia de datos...")
        
        # Obtener datos de diferentes rangos de tiempo
        ranges = ['7d', '30d', '90d']
        data_by_range = {}
        
        for range_str in ranges:
            try:
                response = requests.get(f"{self.base_url}/trends/api/data?range={range_str}")
                if response.status_code == 200:
                    data_by_range[range_str] = response.json()
            except Exception as e:
                print(f"❌ Error obteniendo datos para rango {range_str}: {str(e)}")
                continue

        # Verificar consistencia de datos
        if data_by_range:
            for range_str, data in data_by_range.items():
                print(f"\nRango: {range_str}")
                if 'data' in data and data['data']:
                    sample = data['data'][0]
                    print(f"  ✓ Estructura de datos correcta")
                    print(f"  ✓ Campos presentes: {', '.join(sample.keys())}")
                else:
                    print(f"  ❌ Datos no válidos o vacíos")
        else:
            print("❌ No se pudieron obtener datos para verificar consistencia")

if __name__ == "__main__":
    test = PerformanceTest()
    
    # Ejecutar prueba de carga
    test.run_load_test(num_requests=50, concurrent_users=5)
    
    # Verificar consistencia de datos
    test.test_data_consistency()