from datetime import datetime, timedelta

def parse_date_range(args):
    """
    Parsea el rango de fechas de los argumentos de la petición.
    
    Args:
        args: argumentos de la petición (request.args)
        
    Returns:
        dict: Diccionario con las fechas de inicio y fin
    """
    range_type = args.get('range', '30d')
    end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    if range_type == '7d':
        start_date = end_date - timedelta(days=7)
    elif range_type == '30d':
        start_date = end_date - timedelta(days=30)
    elif range_type == '90d':
        start_date = end_date - timedelta(days=90)
    elif range_type == 'all':
        # Para 'all', usamos una fecha inicial fija
        start_date = datetime(2022, 1, 1)
    else:
        # Si se proporcionan fechas específicas
        try:
            start_date = datetime.strptime(args.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(args.get('end_date'), '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except (ValueError, TypeError):
            # Si hay error en el formato, usar últimos 30 días por defecto
            start_date = end_date - timedelta(days=30)
    
    # Asegurar que start_date comience al inicio del día
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return {
        'start_date': start_date,
        'end_date': end_date
    }

def format_date_for_display(date):
    """
    Formatea una fecha para mostrar en la interfaz.
    
    Args:
        date: objeto datetime
        
    Returns:
        str: Fecha formateada
    """
    return date.strftime('%Y-%m-%d')

def format_date_for_db(date_str):
    """
    Convierte una cadena de fecha al formato de la base de datos.
    
    Args:
        date_str: string de fecha en formato YYYY-MM-DD
        
    Returns:
        datetime: Objeto datetime
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None

def get_date_range_description(range_type):
    """
    Obtiene una descripción legible del rango de fechas.
    
    Args:
        range_type: tipo de rango ('7d', '30d', '90d', 'all')
        
    Returns:
        str: Descripción del rango
    """
    descriptions = {
        '7d': 'Últimos 7 días',
        '30d': 'Últimos 30 días',
        '90d': 'Últimos 90 días',
        'all': 'Todo el período'
    }
    return descriptions.get(range_type, 'Período personalizado')

def generate_date_series(start_date, end_date):
    """
    Genera una serie de fechas entre start_date y end_date.
    
    Args:
        start_date: fecha inicial
        end_date: fecha final
        
    Returns:
        list: Lista de fechas en formato YYYY-MM-DD
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(format_date_for_display(current_date))
        current_date += timedelta(days=1)
        
    return dates

def is_valid_date_range(start_date, end_date):
    """
    Valida que el rango de fechas sea válido.
    
    Args:
        start_date: fecha inicial
        end_date: fecha final
        
    Returns:
        bool: True si el rango es válido
    """
    if not isinstance(start_date, datetime) or not isinstance(end_date, datetime):
        return False
    
    # La fecha inicial debe ser anterior o igual a la final
    if start_date > end_date:
        return False
    
    # El rango no debe ser mayor a 1 año
    if (end_date - start_date).days > 365:
        return False
    
    return True