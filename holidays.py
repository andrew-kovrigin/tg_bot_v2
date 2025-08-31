import feedparser
import logging
from datetime import datetime
import sys
import os
# Add the databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'databases'))

import databases.config as config

logger = logging.getLogger(__name__)

def get_holidays():
    """
    Получение праздников для России через RSS-ленту
    Возвращает список праздников на текущий день.
    """
    try:
        # URL RSS-ленты государственных праздников России
        RSS_URL = config.HOLIDAYS_RSS_URL
        
        # Парсим RSS
        feed = feedparser.parse(RSS_URL)
        
        if feed.bozo and feed.bozo_exception:
            logger.error(f"Ошибка при парсинге RSS: {feed.bozo_exception}")
            return []

        today = datetime.now().strftime("%Y-%m-%d")
        holidays = []

        for entry in feed.entries:
            # Извлекаем дату из поля 'published' (формат: 'Wed, 01 Jan 2025 00:00:00 +0300')
            if 'published' not in entry:
                continue

            try:
                published_date = datetime(*entry.published_parsed[:6])
                entry_date = published_date.strftime("%Y-%m-%d")
            except Exception:
                continue

            # Проверяем, совпадает ли дата записи с сегодняшней
            if entry_date == today:
                holiday = {
                    'name': entry.title.strip(),  # Название праздника
                    'date': entry_date,
                    'type': 'Государственный праздник',
                    'comment': entry.summary.strip() if 'summary' in entry else ''
                }
                holidays.append(holiday)

        logger.info(f"Найдено {len(holidays)} государственных праздников на сегодня.")
        return holidays

    except Exception as e:
        logger.error(f"Ошибка получения данных о праздниках: {str(e)}")
        return []