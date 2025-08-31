import requests
import sys
import os
# Add the databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'databases'))

import databases.config as config
from databases.config import OPENWEATHER_API_KEY, KRASNOYARSK_LAT, KRASNOYARSK_LON
import logging

logger = logging.getLogger(__name__)

def get_weather():
    """
    Получение погоды для Красноярска через OpenWeatherMap API
    """
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': KRASNOYARSK_LAT,
            'lon': KRASNOYARSK_LON,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Извлекаем нужную информацию
        weather_desc = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        
        return {
            'description': weather_desc,
            'temperature': temp,
            'feels_like': feels_like,
            'humidity': humidity,
            'wind_speed': wind_speed
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения данных о погоде: {str(e)}")
        return None