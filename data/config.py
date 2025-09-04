import os
from dotenv import load_dotenv

# Получаем абсолютный путь к .env файлу
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

# Загружаем переменные окружения из файла .env
load_dotenv(env_path, override=True)

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# OpenWeatherMap API Key
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL')

# Адрес для парсинга отключений
OUTAGES_URL = os.getenv('OUTAGES_URL')

# RSS календарь праздников
HOLIDAYS_RSS_URL = os.getenv('HOLIDAYS_RSS_URL')

# Интервал проверки отключений (в часах)
CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', '1'))

# Интервал проверки праздников (в днях)
HOLIDAYS_CHECK_INTERVAL_DAYS = int(os.getenv('HOLIDAYS_CHECK_INTERVAL_DAYS', '1'))

# Интервал проверки погоды (в минутах)
WEATHER_CHECK_INTERVAL_MINUTES = int(os.getenv('WEATHER_CHECK_INTERVAL_MINUTES', '60'))

# URL админ-панели
ADMIN_PANEL_URL = os.getenv('ADMIN_PANEL_URL', 'http://localhost:5000')