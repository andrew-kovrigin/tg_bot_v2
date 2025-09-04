import hashlib
import json

def generate_outage_hash(outage_data):
    """
    Генерирует уникальный хэш для отключения на основе его содержимого.
    
    Args:
        outage_data (dict): Словарь с данными об отключении
        
    Returns:
        str: SHA256 хэш данных об отключении
    """
    # Создаем копию данных для хэширования
    hash_data = {
        'district': outage_data.get('district', ''),
        'resource': outage_data.get('resource', ''),
        'organization': outage_data.get('organization', ''),
        'phone': outage_data.get('phone', ''),
        'addresses': sorted(outage_data.get('addresses', []), key=lambda x: x.get('street', '') if isinstance(x, dict) else ''),
        'reason': outage_data.get('reason', ''),
        'start': outage_data.get('start', ''),
        'end': outage_data.get('end', '')
    }
    
    # Преобразуем в строку и генерируем хэш
    data_string = json.dumps(hash_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()