import os
from dotenv import load_dotenv
import hashlib

load_dotenv()

# Конфигурация Telegram бота
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Конфигурация OpenWeatherMap
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
KRASNOYARSK_LAT = 56.0155
KRASNOYARSK_LON = 92.8692

# Путь к базе данных
DATABASE_URL = 'sqlite:///bot_data.db'

# URL для получения информации об отключениях
DISCONNECTIONS_URL = 'http://93.92.65.26/aspx/Gorod.htm'

# URL для получения информации о праздниках
HOLIDAYS_RSS_URL = 'https://www.calend.ru/rss/russtate.rss'

# Пароль для доступа к админке (хэш SHA512)
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')

# Путь к файлу-флагу для обновления планировщика
SCHEDULER_FLAG_FILE = 'scheduler_update.flag'

# Путь к временному HTML-файлу для парсинга отключений
DISCONNECTIONS_HTML_FILE = 'parse.html'

def hash_password(password):
    """Создает SHA512 хэш от пароля"""
    return hashlib.sha512(password.encode('utf-8')).hexdigest()