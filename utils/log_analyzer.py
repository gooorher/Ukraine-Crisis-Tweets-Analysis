import os
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import logging
from pymongo import MongoClient
import seaborn as sns

class LogAnalyzer:
    """Clase para analizar logs de la aplicación"""
    
    def __init__(self, log_dir='logs', mongo_uri=None):
        """
        Inicializa el analizador de logs
        
        Args:
            log_dir: Directorio donde se encuentran los logs
            mongo_uri: URI de MongoDB para logs en base de datos
        """
        self.log_dir = log_dir
        self.mongo_uri = mongo_uri
        self.logger = logging.getLogger(__name__)
    
    def load_file_logs(self, log_file):
        """
        Carga logs desde un archivo
        
        Args:
            log_file: Nombre del archivo de log
            
        Returns:
            list: Lista de entradas de log
        """
        logs = []
        file_path = os.path.join(self.log_dir, log_file)
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        # Intentar parsear como JSON primero
                        log_entry = json.loads(line)
                    except json.JSONDecodeError:
                        # Si no es JSON, parsear formato estándar
                        log_entry = self._parse_standard_log(line)
                    
                    if log_entry:
                        logs.append(log_entry)
        except Exception as e:
            self.logger.error(f"Error al cargar {log_file}: {str(e)}")
        
        return logs
    
    def load_db_logs(self, start_date=None, end_date=None):
        """
        Carga logs desde MongoDB
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            
        Returns:
            list: Lista de entradas de log
        """
        if not self.mongo_uri:
            self.logger.error("URI de MongoDB no configurada")
            return []
        
        try:
            client = MongoClient(self.mongo_uri)
            db = client.get_default_database()
            
            query = {}
            if start_date or end_date:
                query['timestamp'] = {}
                if start_date:
                    query['timestamp']['$gte'] = start_date
                if end_date:
                    query['timestamp']['$lte'] = end_date
            
            return list(db.logs.find(query))
        except Exception as e:
            self.logger.error(f"Error al cargar logs de MongoDB: {str(e)}")
            return []
    
    def analyze_error_distribution(self, logs):
        """
        Analiza la distribución de errores
        
        Args:
            logs: Lista de entradas de log
            
        Returns:
            dict: Estadísticas de errores
        """
        error_stats = defaultdict(int)
        
        for log in logs:
            if isinstance(log.get('level'), str) and 'ERROR' in log['level']:
                error_type = log.get('error_type', 'Unknown')
                error_stats[error_type] += 1
        
        return dict(error_stats)
    
    def analyze_request_patterns(self, logs):
        """
        Analiza patrones de requests
        
        Args:
            logs: Lista de entradas de log
            
        Returns:
            dict: Estadísticas de requests
        """
        patterns = {
            'endpoints': defaultdict(int),
            'methods': defaultdict(int),
            'status_codes': defaultdict(int),
            'hourly_distribution': defaultdict(int)
        }
        
        for log in logs:
            if 'method' in log:
                patterns['methods'][log['method']] += 1
                patterns['endpoints'][log.get('path', 'unknown')] += 1
                patterns['status_codes'][str(log.get('status', 'unknown'))] += 1
                
                if 'timestamp' in log:
                    hour = self._get_hour(log['timestamp'])
                    patterns['hourly_distribution'][hour] += 1
        
        return {k: dict(v) for k, v in patterns.items()}
    
    def generate_time_series(self, logs, interval='1H'):
        """
        Genera series temporales de eventos
        
        Args:
            logs: Lista de entradas de log
            interval: Intervalo de tiempo para agrupar
            
        Returns:
            pd.DataFrame: DataFrame con series temporales
        """
        # Convertir logs a DataFrame
        df = pd.DataFrame(logs)
        
        if 'timestamp' not in df.columns:
            return pd.DataFrame()
        
        # Convertir timestamp a datetime si es necesario
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Agrupar por intervalo
        return df.set_index('timestamp').resample(interval).count()
    
    def plot_error_distribution(self, error_stats, output_file=None):
        """
        Genera gráfico de distribución de errores
        
        Args:
            error_stats: Estadísticas de errores
            output_file: Archivo de salida para el gráfico
        """
        plt.figure(figsize=(12, 6))
        plt.bar(error_stats.keys(), error_stats.values())
        plt.xticks(rotation=45)
        plt.title('Distribución de Errores')
        plt.xlabel('Tipo de Error')
        plt.ylabel('Cantidad')
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
        else:
            plt.show()
    
    def plot_request_patterns(self, patterns, output_file=None):
        """
        Genera gráfico de patrones de requests
        
        Args:
            patterns: Estadísticas de requests
            output_file: Archivo de salida para el gráfico
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Endpoints más comunes
        top_endpoints = dict(sorted(patterns['endpoints'].items(), 
                                 key=lambda x: x[1], reverse=True)[:10])
        sns.barplot(x=list(top_endpoints.values()), 
                   y=list(top_endpoints.keys()), ax=ax1)
        ax1.set_title('Top 10 Endpoints')
        
        # Métodos HTTP
        sns.barplot(x=list(patterns['methods'].values()),
                   y=list(patterns['methods'].keys()), ax=ax2)
        ax2.set_title('Métodos HTTP')
        
        # Códigos de estado
        sns.barplot(x=list(patterns['status_codes'].values()),
                   y=list(patterns['status_codes'].keys()), ax=ax3)
        ax3.set_title('Códigos de Estado')
        
        # Distribución por hora
        hours = range(24)
        counts = [patterns['hourly_distribution'].get(h, 0) for h in hours]
        ax4.plot(hours, counts)
        ax4.set_title('Distribución por Hora')
        ax4.set_xlabel('Hora')
        ax4.set_ylabel('Requests')
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file)
        else:
            plt.show()
    
    def generate_report(self, start_date=None, end_date=None, output_dir='reports'):
        """
        Genera un reporte completo de análisis de logs
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            output_dir: Directorio para guardar el reporte
        """
        # Crear directorio si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Cargar logs
        file_logs = self.load_file_logs('flask_app.log')
        db_logs = self.load_db_logs(start_date, end_date)
        all_logs = file_logs + db_logs
        
        # Análisis
        error_stats = self.analyze_error_distribution(all_logs)
        request_patterns = self.analyze_request_patterns(all_logs)
        time_series = self.generate_time_series(all_logs)
        
        # Generar gráficos
        self.plot_error_distribution(
            error_stats,
            os.path.join(output_dir, 'error_distribution.png')
        )
        self.plot_request_patterns(
            request_patterns,
            os.path.join(output_dir, 'request_patterns.png')
        )
        
        # Generar reporte HTML
        report_path = os.path.join(output_dir, 'report.html')
        self._generate_html_report(
            report_path,
            {
                'error_stats': error_stats,
                'request_patterns': request_patterns,
                'time_series': time_series
            }
        )
        
        return report_path
    
    def _parse_standard_log(self, line):
        """
        Parsea una línea de log en formato estándar
        
        Args:
            line: Línea de log
            
        Returns:
            dict: Entrada de log parseada
        """
        try:
            # Formato: [timestamp] level in module: message
            parts = line.strip().split(' in ')
            if len(parts) != 2:
                return None
            
            timestamp_level = parts[0].strip('[]').split()
            module_message = parts[1].split(': ', 1)
            
            return {
                'timestamp': datetime.strptime(' '.join(timestamp_level[:-1]),
                                            '%Y-%m-%d %H:%M:%S,%f'),
                'level': timestamp_level[-1],
                'module': module_message[0],
                'message': module_message[1] if len(module_message) > 1 else ''
            }
        except Exception:
            return None
    
    def _get_hour(self, timestamp):
        """
        Extrae la hora de un timestamp
        
        Args:
            timestamp: Timestamp en varios formatos posibles
            
        Returns:
            int: Hora (0-23)
        """
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, (float, int)):
            timestamp = datetime.fromtimestamp(timestamp)
        
        return timestamp.hour
    
    def _generate_html_report(self, output_file, data):
        """
        Genera un reporte HTML
        
        Args:
            output_file: Ruta del archivo de salida
            data: Datos para el reporte
        """
        template = """
        <html>
        <head>
            <title>Análisis de Logs</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #2c3e50; }
                .section { margin: 20px 0; padding: 20px; border: 1px solid #eee; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border: 1px solid #ddd; }
                th { background-color: #f5f5f5; }
                img { max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Reporte de Análisis de Logs</h1>
            
            <div class="section">
                <h2>Distribución de Errores</h2>
                <img src="error_distribution.png" alt="Distribución de Errores">
                <table>
                    <tr><th>Tipo de Error</th><th>Cantidad</th></tr>
                    {error_rows}
                </table>
            </div>
            
            <div class="section">
                <h2>Patrones de Requests</h2>
                <img src="request_patterns.png" alt="Patrones de Requests">
                <h3>Top 10 Endpoints</h3>
                <table>
                    <tr><th>Endpoint</th><th>Cantidad</th></tr>
                    {endpoint_rows}
                </table>
            </div>
            
            <div class="section">
                <h2>Estadísticas Generales</h2>
                <table>
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    {stats_rows}
                </table>
            </div>
        </body>
        </html>
        """
        
        # Generar filas de la tabla de errores
        error_rows = '\n'.join(
            f'<tr><td>{error}</td><td>{count}</td></tr>'
            for error, count in data['error_stats'].items()
        )
        
        # Generar filas de la tabla de endpoints
        endpoint_rows = '\n'.join(
            f'<tr><td>{endpoint}</td><td>{count}</td></tr>'
            for endpoint, count in sorted(
                data['request_patterns']['endpoints'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        )
        
        # Generar filas de estadísticas generales
        total_requests = sum(data['request_patterns']['endpoints'].values())
        total_errors = sum(data['error_stats'].values())
        stats_rows = f"""
            <tr><td>Total de Requests</td><td>{total_requests}</td></tr>
            <tr><td>Total de Errores</td><td>{total_errors}</td></tr>
            <tr><td>Tasa de Error</td><td>{(total_errors/total_requests)*100:.2f}%</td></tr>
        """
        
        # Generar HTML
        html = template.format(
            error_rows=error_rows,
            endpoint_rows=endpoint_rows,
            stats_rows=stats_rows
        )
        
        # Guardar reporte
        with open(output_file, 'w') as f:
            f.write(html)