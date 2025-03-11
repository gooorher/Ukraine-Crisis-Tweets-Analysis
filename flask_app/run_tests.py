#!/usr/bin/env python3
import unittest
import subprocess
import time
import sys
from datetime import datetime

def print_header(text):
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")

def run_command(command, wait=True):
    """Ejecuta un comando y retorna su salida"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    if wait:
        stdout, stderr = process.communicate()
        return stdout.decode(), stderr.decode(), process.returncode
    return None, None, process.pid

def start_flask():
    """Inicia la aplicación Flask en segundo plano"""
    print("Iniciando aplicación Flask...")
    _, _, pid = run_command("python app.py &", wait=False)
    time.sleep(5)  # Esperar a que Flask inicie
    return pid

def stop_flask(pid):
    """Detiene la aplicación Flask"""
    print("\nDeteniendo aplicación Flask...")
    run_command(f"pkill -f 'python app.py'")

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        def log(message):
            print(message)
            f.write(message + "\n")
            f.flush()

        print_header("EJECUTANDO PRUEBAS COMPLETAS")
        log(f"Fecha y hora: {datetime.now()}")
        
        try:
            # 1. Prueba de conexión a MongoDB
            print_header("1. Prueba de conexión a MongoDB")
            stdout, stderr, returncode = run_command("python test_mongodb.py")
            log(stdout)
            if stderr:
                log("Errores:\n" + stderr)
            
            # 2. Prueba de recuperación de datos
            print_header("2. Prueba de recuperación de datos")
            stdout, stderr, returncode = run_command("python test_data_retrieval.py")
            log(stdout)
            if stderr:
                log("Errores:\n" + stderr)
            
            # 3. Pruebas unitarias de Flask
            print_header("3. Pruebas unitarias de Flask")
            stdout, stderr, returncode = run_command("python -m unittest test_flask_app.py -v")
            log(stdout)
            if stderr:
                log("Errores:\n" + stderr)
            
            # 4. Pruebas de rendimiento
            print_header("4. Pruebas de rendimiento")
            flask_pid = start_flask()
            stdout, stderr, returncode = run_command("python test_performance.py")
            log(stdout)
            if stderr:
                log("Errores:\n" + stderr)
            stop_flask(flask_pid)
            
            # 5. Monitoreo del sistema
            print_header("5. Monitoreo del sistema")
            flask_pid = start_flask()
            stdout, stderr, returncode = run_command("python monitor.py 30 5")
            log(stdout)
            if stderr:
                log("Errores:\n" + stderr)
            stop_flask(flask_pid)
            
            print_header("RESUMEN DE PRUEBAS")
            log("\nTodas las pruebas han sido completadas.")
            log(f"El informe completo ha sido guardado en: {report_file}")
            
        except Exception as e:
            log(f"\nError durante la ejecución de pruebas: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()