import psutil
import pymongo
import sys
import time
from datetime import datetime
import os

def get_mongodb_stats():
    """Obtiene estadísticas de MongoDB"""
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client['ukraine_crisis']
        
        db_stats = db.command('dbStats')
        collection_stats = {
            'tweets': db.command('collStats', 'tweets'),
            'users': db.command('collStats', 'users')
        }
        
        return {
            'status': 'connected',
            'database_size': db_stats['dataSize'] / (1024 * 1024),  # MB
            'storage_size': db_stats['storageSize'] / (1024 * 1024),  # MB
            'collections': {
                'tweets': {
                    'count': collection_stats['tweets']['count'],
                    'size': collection_stats['tweets']['size'] / (1024 * 1024),  # MB
                    'avg_obj_size': collection_stats['tweets']['avgObjSize']
                },
                'users': {
                    'count': collection_stats['users']['count'],
                    'size': collection_stats['users']['size'] / (1024 * 1024),  # MB
                    'avg_obj_size': collection_stats['users']['avgObjSize']
                }
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_system_stats():
    """Obtiene estadísticas del sistema"""
    return {
        'cpu': {
            'usage_percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'load_avg': psutil.getloadavg()
        },
        'memory': {
            'total': psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
            'available': psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
            'used_percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total / (1024 * 1024 * 1024),  # GB
            'used': psutil.disk_usage('/').used / (1024 * 1024 * 1024),  # GB
            'free': psutil.disk_usage('/').free / (1024 * 1024 * 1024),  # GB
            'used_percent': psutil.disk_usage('/').percent
        }
    }

def get_flask_process():
    """Encuentra el proceso de Flask"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and any('flask' in cmd.lower() for cmd in proc.info['cmdline'] if cmd):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def monitor(duration=60, interval=5):
    """Monitorea la aplicación por un período determinado"""
    print(f"\nIniciando monitoreo del sistema (duración: {duration}s, intervalo: {interval}s)")
    
    end_time = time.time() + duration
    samples = []
    
    while time.time() < end_time:
        timestamp = datetime.now()
        
        # Obtener estadísticas
        mongodb_stats = get_mongodb_stats()
        system_stats = get_system_stats()
        
        # Verificar proceso de Flask
        flask_proc = get_flask_process()
        if flask_proc:
            flask_stats = {
                'status': 'running',
                'pid': flask_proc.pid,
                'cpu_percent': flask_proc.cpu_percent(),
                'memory_percent': flask_proc.memory_percent(),
                'threads': flask_proc.num_threads()
            }
        else:
            flask_stats = {'status': 'not_running'}
        
        # Guardar muestra
        samples.append({
            'timestamp': timestamp,
            'mongodb': mongodb_stats,
            'system': system_stats,
            'flask': flask_stats
        })
        
        # Mostrar estadísticas en tiempo real
        print(f"\nEstadísticas ({timestamp}):")
        print("MongoDB:")
        print(f"  - Estado: {mongodb_stats['status']}")
        if mongodb_stats['status'] == 'connected':
            print(f"  - Tamaño de base de datos: {mongodb_stats['database_size']:.2f} MB")
            print(f"  - Tweets: {mongodb_stats['collections']['tweets']['count']:,}")
            print(f"  - Usuarios: {mongodb_stats['collections']['users']['count']:,}")
        
        print("\nSistema:")
        print(f"  - CPU: {system_stats['cpu']['usage_percent']}%")
        print(f"  - Memoria: {system_stats['memory']['used_percent']}%")
        print(f"  - Disco: {system_stats['disk']['used_percent']}%")
        
        print("\nFlask:")
        print(f"  - Estado: {flask_stats['status']}")
        if flask_stats['status'] == 'running':
            print(f"  - CPU: {flask_stats['cpu_percent']}%")
            print(f"  - Memoria: {flask_stats['memory_percent']:.2f}%")
            print(f"  - Threads: {flask_stats['threads']}")
        
        time.sleep(interval)
    
    return samples

def generate_report(samples):
    """Genera un informe basado en las muestras recolectadas"""
    if not samples:
        return "No hay datos para generar el informe"
    
    report = []
    report.append("\nINFORME DE MONITOREO")
    report.append("=" * 50)
    
    # Período de monitoreo
    start_time = samples[0]['timestamp']
    end_time = samples[-1]['timestamp']
    duration = (end_time - start_time).total_seconds()
    report.append(f"\nPeríodo de monitoreo:")
    report.append(f"  Inicio: {start_time}")
    report.append(f"  Fin: {end_time}")
    report.append(f"  Duración: {duration:.0f} segundos")
    
    # Estadísticas de MongoDB
    mongodb_connected = [s for s in samples if s['mongodb']['status'] == 'connected']
    if mongodb_connected:
        last_mongodb = mongodb_connected[-1]['mongodb']
        report.append("\nEstadísticas de MongoDB:")
        report.append(f"  Base de datos: ukraine_crisis")
        report.append(f"  Tamaño total: {last_mongodb['database_size']:.2f} MB")
        report.append(f"  Tweets almacenados: {last_mongodb['collections']['tweets']['count']:,}")
        report.append(f"  Usuarios almacenados: {last_mongodb['collections']['users']['count']:,}")
    
    # Estadísticas del sistema
    cpu_usage = [s['system']['cpu']['usage_percent'] for s in samples]
    memory_usage = [s['system']['memory']['used_percent'] for s in samples]
    disk_usage = [s['system']['disk']['used_percent'] for s in samples]
    
    report.append("\nEstadísticas del sistema:")
    report.append(f"  CPU:")
    report.append(f"    - Promedio: {sum(cpu_usage) / len(cpu_usage):.1f}%")
    report.append(f"    - Máximo: {max(cpu_usage):.1f}%")
    report.append(f"  Memoria:")
    report.append(f"    - Promedio: {sum(memory_usage) / len(memory_usage):.1f}%")
    report.append(f"    - Máximo: {max(memory_usage):.1f}%")
    report.append(f"  Disco:")
    report.append(f"    - Uso: {disk_usage[-1]:.1f}%")
    
    # Estado de Flask
    flask_running = [s for s in samples if s['flask']['status'] == 'running']
    if flask_running:
        flask_cpu = [s['flask']['cpu_percent'] for s in flask_running]
        flask_memory = [s['flask']['memory_percent'] for s in flask_running]
        
        report.append("\nEstadísticas de Flask:")
        report.append(f"  Estado: Ejecutándose")
        report.append(f"  CPU:")
        report.append(f"    - Promedio: {sum(flask_cpu) / len(flask_cpu):.1f}%")
        report.append(f"    - Máximo: {max(flask_cpu):.1f}%")
        report.append(f"  Memoria:")
        report.append(f"    - Promedio: {sum(flask_memory) / len(flask_memory):.1f}%")
        report.append(f"    - Máximo: {max(flask_memory):.1f}%")
    else:
        report.append("\nFlask no se encuentra en ejecución")
    
    return "\n".join(report)

if __name__ == "__main__":
    try:
        duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    except (IndexError, ValueError):
        duration = 60
        interval = 5
    
    samples = monitor(duration, interval)
    report = generate_report(samples)
    
    print("\nGenerando informe...")
    print(report)
    
    # Guardar informe en archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"monitoring_report_{timestamp}.txt"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"\nInforme guardado en: {report_file}")