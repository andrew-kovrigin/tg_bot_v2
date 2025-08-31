import re
from bs4 import BeautifulSoup

def parse_html(file_path):
    """
    Парсинг HTML-файла с информацией о плановых отключениях
    Возвращает список словарей с данными об отключениях
    """
    # Читаем содержимое файла
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Находим таблицу
    table = soup.find('table')
    if not table:
        raise ValueError("Таблица не найдена в HTML-файле")
    
    # Получаем все строки таблицы (кроме заголовков)
    rows = table.find_all('tr')[2:]  # Пропускаем заголовки и строку с районом
    
    results = []
    
    for row in rows:
        # Получаем ячейки строки
        cells = row.find_all('td')
        if len(cells) < 3:
            continue
            
        # Извлекаем данные из ячеек
        resource_org_cell = cells[0]
        addresses_reason_cell = cells[1]
        period_cell = cells[2]
        
        # Извлекаем текст из ячеек
        resource_org_text = resource_org_cell.get_text(strip=True)
        addresses_reason_text = addresses_reason_cell.get_text(strip=True)
        period_text = period_cell.get_text(strip=True)
        
        # Разделяем информацию по строкам для более точного извлечения
        resource_lines = resource_org_text.split('\n')
        address_lines = addresses_reason_text.split('\n')
        period_lines = period_text.split('\n')
        
        # Извлекаем основную информацию
        resource = resource_lines[0].strip() if resource_lines else ""

        # Организация и контактные данные
        org_info = ""
        if len(resource_lines) > 1:
            org_info = resource_lines[1].strip()
            
        # Обработка адресов и причины
        addresses = []
        reason = ""
        
        # Собираем адреса и причину из строк
        address_reason_text = ' '.join([line.strip() for line in address_lines if line.strip()])
        
        # Ищем причину в тексте
        reason_keywords = ['плановое', 'авария', 'аварийное', 'прочее', 'иное', 'отмена']
        reason_start = -1
        
        # Находим позицию начала причины
        for keyword in reason_keywords:
            pos = address_reason_text.lower().find(keyword)
            if pos != -1:
                if reason_start == -1 or pos < reason_start:
                    reason_start = pos
                    
        # Если нашли причину, определяем ее границы
        if reason_start != -1:
            # Адреса - это текст до причины
            address_part = address_reason_text[:reason_start].strip()
            # Причина - это текст начиная с найденной причины
            reason = address_reason_text[reason_start:].strip()
        else:
            # Если причина не найдена, считаем весь текст адресами
            address_part = address_reason_text
            reason = ""
            
        # Разбиваем адреса, учитывая сложные случаи
        if address_part:
            # Сначала разделяем по точке с запятой
            parts = address_part.split(';')
            
            # Обрабатываем каждую часть
            for part in parts:
                part = part.strip()
                if part:
                    # Проверяем, содержит ли часть несколько адресов, разделенных запятыми
                    # Более точная проверка на необходимость разделения по запятым
                    if ',' in part:
                        # Не разделяем по запятым, если это часть адреса с номером или строением
                        skip_split = any(keyword in part.lower() for keyword in [
                            'стр.', 'а/', 'а\\', 'к.', 'кв.', 'д.', 'ул.', 'пер.', 'пр.', 'пр-т', 'бул.', 'пл.', 'наб.', 'ал.', 'мкр.', 'тер.', 'р-н'
                        ])
                        
                        if not skip_split:
                            # Разделяем по запятым
                            subparts = part.split(',')
                            for subpart in subparts:
                                subpart = subpart.strip()
                                if subpart:
                                    # Дополнительная проверка, чтобы не разделять составные части адресов
                                    if len(subpart.split()) > 1 or any(c.isdigit() for c in subpart):
                                        addresses.append(subpart)
                                    elif subpart:
                                        addresses.append(subpart)
                        else:
                            addresses.append(part)
                    else:
                        addresses.append(part)
            
        # Очищаем адреса от пустых значений
        addresses = [addr for addr in addresses if addr.strip()]
            
        # Периоды
        periods = []
        for line in period_lines:
            if line.strip() and line.strip() != '&nbsp;':
                periods.append(line.strip())
                
        # Создаем словарь с данными только если есть адреса или причина
        # И если запись содержит осмысленные данные
        if (addresses or reason) and (resource or org_info or addresses or reason):
            result = {
                'resource': resource,
                'organization': org_info,
                'addresses': addresses,
                'reason': reason,
                'periods': periods
            }
            
            results.append(result)
    
    return results