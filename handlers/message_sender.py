#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message sending functions
"""
import logging
import traceback
from databases.models import Group, SchedulerSettings, get_db
import weather
import holidays
import disconnections

logger = logging.getLogger(__name__)

async def send_scheduled_message(bot, message_type):
    """Универсальная функция отправки запланированных сообщений"""
    logger.info(f"Отправка запланированного сообщения типа: {message_type}")
    
    db = next(get_db())
    try:
        # Проверяем настройки планировщика
        scheduler_setting = db.query(SchedulerSettings).filter(
            SchedulerSettings.job_type == message_type
        ).first()
        
        if not scheduler_setting or not scheduler_setting.is_enabled:
            logger.info(f"Сообщения типа {message_type} отключены в настройках")
            return
            
        # Определяем группы для отправки
        if scheduler_setting.target_groups:
            # Если указаны конкретные группы, отправляем только в них
            group_ids = [gid.strip() for gid in scheduler_setting.target_groups.split(',')]
            groups = db.query(Group).filter(Group.group_id.in_(group_ids)).all()
        else:
            # Если группы не указаны, отправляем во все активные группы
            groups = db.query(Group).filter(Group.is_active == True).all()
            
        if not groups:
            logger.info("Нет групп для отправки сообщений")
            return
            
        # Формируем сообщение в зависимости от типа
        message_text = ""
        if message_type == "daily_message":
            # Получаем данные для отправки
            weather_data = weather.get_weather()
            holidays_data = holidays.get_holidays()
            disconnections_data = disconnections.get_disconnections()
            
            # Формируем сообщение
            message_text = "Ежедневное оповещение:\n\n"
            
            # Погода
            if weather_data:
                message_text += "Погода в Красноярске:\n"
                message_text += f"Описание: {weather_data['description']}\n"
                message_text += f"Температура: {weather_data['temperature']}°C\n\n"
            
            # Праздники
            if holidays_data:
                message_text += "Праздники сегодня:\n"
                for holiday in holidays_data:
                    message_text += f"• {holiday['name']}\n"
                message_text += "\n"
            else:
                message_text += "Сегодня нет праздников\n\n"
            
            # Отключения
            if disconnections_data:
                message_text += "Отключения на ближайшие дни:\n"
                for disconnect in disconnections_data[:3]:  # Показываем первые 3 записи
                    message_text += f"Дата: {disconnect['date'].strftime('%d.%m.%Y %H:%M')}\n"
                    message_text += f"Адрес: {disconnect['address']}\n"
                    message_text += f"Описание: {disconnect['description']}\n\n"
            else:
                message_text += "Информация об отключениях отсутствует\n\n"
                
        elif message_type == "weather":
            weather_data = weather.get_weather()
            if weather_data:
                message_text = "Погода в Красноярске:\n\n"
                message_text += f"Описание: {weather_data['description']}\n"
                message_text += f"Температура: {weather_data['temperature']}°C\n"
                message_text += f"Ощущается как: {weather_data['feels_like']}°C\n"
                message_text += f"Влажность: {weather_data['humidity']}%\n"
                message_text += f"Скорость ветра: {weather_data['wind_speed']} м/с"
            else:
                message_text = "Не удалось получить информацию о погоде"
                
        elif message_type == "holidays":
            holidays_data = holidays.get_holidays()
            if holidays_data:
                message_text = "Праздники на сегодня:\n\n"
                for holiday in holidays_data:
                    message_text += f"• {holiday['name']}\n"
                    if holiday['comment']:
                        message_text += f"  {holiday['comment'][:100]}...\n"
                    message_text += "\n"
            else:
                message_text = "На сегодня праздников нет"
                
        elif message_type == "disconnections":
            disconnections_data = disconnections.get_disconnections()
            if disconnections_data:
                message_text = "Отключения на ближайшие дни:\n\n"
                for disconnect in disconnections_data[:5]:  # Показываем первые 5 записей
                    message_text += f"Дата: {disconnect['date'].strftime('%d.%m.%Y %H:%M')}\n"
                    message_text += f"Адрес: {disconnect['address']}\n"
                    message_text += f"Описание: {disconnect['description']}\n\n"
            else:
                message_text = "Информация об отключениях отсутствует"
        
        # Отправляем сообщения в каждую группу
        sent_count = 0
        for group in groups:
            try:
                await bot.send_message(group.group_id, message_text)
                logger.info(f"Сообщение типа {message_type} отправлено в группу {group.group_name}")
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения в группу {group.group_name}: {str(e)}")
                
        logger.info(f"Завершена отправка сообщений типа {message_type}. Отправлено в {sent_count} групп из {len(groups)}")
                
    except Exception as e:
        logger.error(f"Ошибка при отправке запланированного сообщения типа {message_type}: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
    finally:
        db.close()