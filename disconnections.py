import requests
import logging
from datetime import datetime
from utils.parse import parse_html
import sys
import os
# Add the databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'databases'))

from databases.models import Group, Disconnection, get_db
import databases.config as config

logger = logging.getLogger(__name__)

def get_disconnections():
    """
    Получение информации об отключениях из указанного источника с использованием нового парсера
    Возвращает данные в формате, совместимом с ботом
    """
    try:
        # Получаем данные с сайта
        response = requests.get(config.DISCONNECTIONS_URL, timeout=10)
        response.encoding = 'windows-1251'  # Устанавливаем кодировку
        
        # Сохраняем HTML для парсинга
        with open(config.DISCONNECTIONS_HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Используем новый парсер
        parsed_data = parse_html(config.DISCONNECTIONS_HTML_FILE)
        logger.info(f"Успешно спарсили {len(parsed_data)} записей")
        
        # Преобразуем данные в формат, совместимый с ботом
        # Бот ожидает: date, address, description
        compatible_data = []
        
        # Получаем список адресов из админки (групп)
        db = next(get_db())
        try:
            groups = db.query(Group).filter(Group.address.isnot(None)).filter(Group.address != '').all()
            admin_addresses = {}
            for group in groups:
                # Разбиваем адреса на отдельные элементы, если их несколько
                addresses = group.address.split(';') if ';' in group.address else [group.address]
                for addr in addresses:
                    addr = addr.strip()
                    if addr not in admin_addresses:
                        admin_addresses[addr] = []
                    admin_addresses[addr].append({
                        'group_id': group.group_id,
                        'group_name': group.group_name
                    })
        finally:
            db.close()
        
        # Сохраняем все отключения в базу данных
        db = next(get_db())
        try:
            # Сначала удалим старые записи за сегодня (если есть)
            today = datetime.today().date()
            db.query(Disconnection).filter(
                Disconnection.date >= datetime.combine(today, datetime.min.time()),
                Disconnection.date <= datetime.combine(today, datetime.max.time())
            ).delete(synchronize_session=False)
            
            # Сохраняем новые отключения
            saved_count = 0
            for record in parsed_data:
                addresses = record.get('addresses', [])
                reason = record.get('reason', '')
                periods = record.get('periods', [])
                
                # Для каждой записи создаем отдельные записи для каждого адреса
                for address in addresses:
                    # Проверяем, есть ли этот адрес в списках групп
                    clean_address = address.strip().lower()
                    matched_groups = []
                    for admin_addr, group_info_list in admin_addresses.items():
                        # Проверяем частичное совпадение (включая подстроки)
                        if clean_address in admin_addr.lower() or admin_addr.lower() in clean_address:
                            matched_groups.extend(group_info_list)
                    
                    # Если адрес есть в списках групп, сохраняем отключение
                    if matched_groups:
                        # Создаем "фиктивную" дату, т.к. в новых данных нет точной даты
                        # Используем сегодняшнюю дату
                        fake_date = datetime.now()
                        
                        # Создаем запись в базе данных
                        disconnection = Disconnection(
                            group_id=matched_groups[0]['group_id'],  # Берем первый совпадающий group_id
                            address=address,
                            description=f"{record.get('resource', '')} - {reason}".strip(),
                            date=fake_date
                        )
                        db.add(disconnection)
                        saved_count += 1
                        
                        # Добавляем в данные для бота (только для адресов из групп)
                        disconnection_data = {
                            'date': fake_date,
                            'address': address,
                            'description': f"{record.get('resource', '')} - {reason}".strip()
                        }
                        compatible_data.append(disconnection_data)
            
            db.commit()
            logger.info(f"Сохранено {saved_count} отключений в базу данных")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении отключений в базу: {str(e)}")
            db.rollback()
        finally:
            db.close()
        
        logger.info(f"Подготовлено {len(compatible_data)} записей в формате для бота")
        return compatible_data
        
    except Exception as e:
        logger.error(f"Ошибка получения данных об отключениях: {str(e)}")
        return []

