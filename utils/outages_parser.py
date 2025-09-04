# Модуль для парсинга отключений
import re
import requests
import logging
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
from data.config import OUTAGES_URL

# Настройка логирования
logger = logging.getLogger(__name__)

# --- Константы для улучшения читаемости и поддержки ---
DISTRICT_BG_COLORS = {"#0069d2", "#0058b3"}
DATA_ROW_BG_COLORS = {None, "#ddebf7", "#ffffff"}

# Регулярные выражения, скомпилированные для производительности
PHONE_PATTERN = re.compile(r'(?:т\.\s*)?(\d[\d\s\-().]{8,})')
WHITESPACE_PATTERN = re.compile(r'\s+')
STREET_HOUSE_SPLIT_PATTERN = re.compile(r'[,;]\s*')
HOUSE_NUMBER_START_PATTERN = re.compile(r'^\d')
REASON_KEYWORDS = ('аварийное', 'плановое')
RGB_PATTERN = re.compile(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)')


def _clean_text(text: str) -> str:
    """Удаляет лишние пробелы и пробелы по краям строки."""
    if not text:
        return ""
    return WHITESPACE_PATTERN.sub(' ', text).strip()


def normalize_color(color_str: Optional[str]) -> Optional[str]:
    """Нормализует цвет в hex-формат (если возможно)."""
    if not color_str:
        return None
    color_str = color_str.lower()
    if color_str.startswith('#'):
        return color_str
    rgb_match = RGB_PATTERN.match(color_str)
    if rgb_match:
        try:
            r, g, b = map(int, rgb_match.groups())
            return f'#{r:02x}{g:02x}{b:02x}'
        except ValueError:
            logger.warning(f"Невозможно преобразовать RGB цвет: {color_str}")
            return None
    return None


def get_background_color(element: BeautifulSoup) -> Optional[str]:
    """Извлекает и нормализует цвет фона из стиля элемента."""
    if not element:
        return None
        
    style = element.get('style', '')
    # Объединенный паттерн для одного поиска
    pattern = (
        r'background(?:-color)?:\s*(#[0-9a-fA-F]{6}|rgb\(\d+,\s*\d+,\s*\d+\))|'
        r'mso-pattern:\s*(#[0-9a-fA-F]{6})\s+none'
    )
    match = re.search(pattern, style, re.IGNORECASE)
    if match:
        # Находим первую совпавшую группу, которая не None
        color = next((g for g in match.groups() if g), None)
        return normalize_color(color)
    return None


def parse_resource_organization(cell_tag: BeautifulSoup) -> Dict[str, str]:
    """Парсит ячейку с ресурсом, организацией и телефоном за один проход."""
    try:
        if not cell_tag:
            return {"resource": "", "organization": "", "phone": ""}
            
        text_parts = list(cell_tag.stripped_strings)
        if not text_parts:
            return {"resource": "", "organization": "", "phone": ""}

        resource = text_parts[0].strip()
        # Все остальное - потенциально организация и телефон
        org_phone_text = _clean_text(" ".join(text_parts[1:]))

        organization = org_phone_text
        phone = ""

        phone_match = PHONE_PATTERN.search(org_phone_text)
        if phone_match:
            phone = _clean_text(phone_match.group(1))
            # Удаляем найденный телефон из строки организации
            organization = _clean_text(PHONE_PATTERN.sub('', org_phone_text, 1))

        return {
            "resource": resource,
            "organization": organization,
            "phone": phone
        }
    except Exception as e:
        logger.error(f"Ошибка при парсинге ресурса/организации: {e}")
        return {"resource": "", "organization": "", "phone": ""}


def _parse_address_block(block: str) -> Dict[str, Any]:
    """Парсит один блок адреса (улица и дома)."""
    try:
        block = block.strip()
        if not block:
            return {"street": "", "houses": []}

        # Обработка блока с разделителем ':'
        if ':' in block:
            parts = block.split(':', 1)
            if len(parts) == 2:
                street_part, houses_part = parts
                street = _clean_text(street_part)
                houses = [
                    h.strip().rstrip(',;')
                    for h in STREET_HOUSE_SPLIT_PATTERN.split(houses_part) if h.strip()
                ]
            else:
                street = _clean_text(block)
                houses = []
        else:
            # "Умный" парсинг без разделителя
            tokens = block.split()
            street_tokens, house_tokens = [], []
            found_number = False

            for token in tokens:
                # Определяем, где заканчивается улица и начинаются номера домов
                cleaned_token = token.rstrip(',;')
                if not found_number and HOUSE_NUMBER_START_PATTERN.match(cleaned_token):
                    found_number = True
                (house_tokens if found_number else street_tokens).append(token)
            
            street = _clean_text(" ".join(street_tokens))
            houses_text = " ".join(house_tokens)
            houses = [
                h.strip() for h in STREET_HOUSE_SPLIT_PATTERN.split(houses_text) if h.strip()
            ]

        return {"street": street, "houses": houses}
    except Exception as e:
        logger.error(f"Ошибка при парсинге адресного блока: {e}")
        return {"street": "", "houses": []}


def parse_addresses_and_reason(cell_tag: BeautifulSoup) -> Dict[str, Any]:
    """
    Парсит ячейку с адресами и причиной отключения.
    Упрощенная и более надежная логика.
    """
    try:
        if not cell_tag:
            return {"addresses": [], "reason": ""}
            
        text = cell_tag.get_text(separator='\\n', strip=True)
        lines = [line for line in text.split('\\n') if line]
        
        address_lines, reason_lines = [], []
        reason_found = False

        for line in lines:
            if not reason_found and line.lower().startswith(REASON_KEYWORDS):
                reason_found = True
            (reason_lines if reason_found else address_lines).append(line)
            
        address_text = _clean_text(" ".join(address_lines))
        reason = _clean_text(" ".join(reason_lines))
        
        addresses = []
        for block in re.split(r';\s*', address_text):
            parsed_block = _parse_address_block(block)
            if parsed_block["street"]:
                addresses.append(parsed_block)
        
        return {"addresses": addresses, "reason": reason}
    except Exception as e:
        logger.error(f"Ошибка при парсинге адресов и причины: {e}")
        return {"addresses": [], "reason": ""}


def parse_time(cell_tag: BeautifulSoup) -> Dict[str, str]:
    """Парсит ячейку с временем начала и окончания."""
    try:
        if not cell_tag:
            return {"start": "", "end": ""}
            
        lines = list(cell_tag.stripped_strings)
        
        if not lines:
            return {"start": "", "end": ""}
        
        if len(lines) == 1 and "отмена" in lines[0].lower():
            return {"start": "отмена", "end": "отмена"}
        
        start = _clean_text(lines[0])
        end = _clean_text(lines[1]) if len(lines) >= 2 else ""
        return {"start": start, "end": end}
    except Exception as e:
        logger.error(f"Ошибка при парсинге времени: {e}")
        return {"start": "", "end": ""}


def fetch_outages_html() -> str:
    """Получает HTML с данными об отключениях."""
    try:
        if not OUTAGES_URL:
            raise Exception("URL для получения данных об отключениях не установлен")
            
        logger.info(f"Получение данных об отключениях с {OUTAGES_URL}")
        response = requests.get(OUTAGES_URL, timeout=30)
        response.raise_for_status()
        # Явно устанавливаем кодировку windows-1251, так как сайт отдает данные в этой кодировке
        response.encoding = 'windows-1251'
        logger.info("Данные об отключениях успешно получены")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Ошибка сети при получении данных об отключениях: {str(e)}")
        raise Exception(f"Ошибка сети при получении данных об отключениях: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при получении данных об отключениях: {str(e)}")
        raise Exception(f"Ошибка при получении данных об отключениях: {str(e)}")


def parse_outages() -> List[Dict[str, Any]]:
    """Основная функция для парсинга HTML и возврата результатов."""
    try:
        logger.info("Начало парсинга отключений")
        content = fetch_outages_html()
    except Exception as e:
        logger.error(f"Ошибка при получении HTML: {e}")
        raise e

    # Проверяем наличие lxml для ускорения парсинга
    try:
        import lxml  # noqa: F401
        parser = 'lxml'
        logger.debug("Используется парсер lxml")
    except ImportError:
        parser = 'html.parser'
        logger.debug("Используется парсер html.parser")
    
    try:
        soup = BeautifulSoup(content, parser)
        table = soup.find('table')
        if not table:
            logger.error("Таблица не найдена в HTML файле")
            raise Exception("Таблица не найдена в HTML файле.")
        
        logger.debug("Таблица найдена, начинаем парсинг строк")
        
        outages_data = []
        current_district = "Не определен"
        
        rows = table.find_all('tr')  # Извлекаем все строки один раз
        logger.debug(f"Найдено {len(rows)} строк в таблице")
        
        for i, row in enumerate(rows):
            try:
                # Пропускаем невидимые строки
                style = row.get('style', '')
                if 'display:none' in style or row.get('height') == '0':
                    continue
                    
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                
                # Вычисляем цвета фона заранее для оптимизации
                first_cell_bg = get_background_color(cells[0])
                data_cell_bg = get_background_color(cells[1])
                
                # Определяем район по цвету фона
                if first_cell_bg in DISTRICT_BG_COLORS:
                    district_text = cells[1].get_text(strip=True)
                    if "район" in district_text:
                        current_district = _clean_text(district_text)
                        logger.debug(f"Найден район: {current_district}")
                    continue
                
                # Пропускаем информационные заголовки
                second_cell_text = cells[1].get_text(strip=True)
                if ("Запланированные отключения" in second_cell_text or
                    "Плановые отключения на" in second_cell_text):
                    continue
                
                # Парсим строки с данными
                if data_cell_bg in DATA_ROW_BG_COLORS and first_cell_bg in DATA_ROW_BG_COLORS:
                    logger.debug(f"Парсинг строки {i} как данных об отключении")
                    parsed_resource = parse_resource_organization(cells[0])
                    parsed_address = parse_addresses_and_reason(cells[1])
                    parsed_time = parse_time(cells[2])
                    
                    outage_entry = {
                        "district": current_district,
                        "resource": parsed_resource["resource"],
                        "organization": parsed_resource["organization"],
                        "phone": parsed_resource["phone"],
                        "addresses": parsed_address["addresses"],
                        "reason": parsed_address["reason"],
                        "start": parsed_time["start"],
                        "end": parsed_time["end"]
                    }
                    outages_data.append(outage_entry)
                    logger.debug(f"Добавлено отключение: {outage_entry['district']} - {outage_entry['resource']}")
            except Exception as e:
                logger.warning(f"Ошибка при парсинге строки {i}: {e}")
                continue
        
        logger.info(f"Парсинг завершен. Найдено {len(outages_data)} записей об отключениях")
        
        if not outages_data:
            logger.warning("Данные об отключениях не найдены")
            raise Exception("Данные об отключениях не найдены.")
        
        return outages_data
    except Exception as e:
        logger.error(f"Критическая ошибка при парсинге отключений: {e}")
        raise Exception(f"Критическая ошибка при парсинге отключений: {str(e)}")