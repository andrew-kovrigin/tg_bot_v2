#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command handlers for the bot
"""
import logging
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from databases.models import Group, UserRequest, get_db
import weather
import holidays
import disconnections

logger = logging.getLogger(__name__)

def register_command_handlers(dp, bot):
    """Register all command handlers"""
    
    # Команда /start
    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer("Привет! Я бот для оповещения о погоде, праздниках и отключениях.")
    
    # Команда /help
    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        help_text = """
Доступные команды:
/start - Начать работу с ботом
/help - Показать помощь
/weather - Получить информацию о погоде
/holidays - Получить информацию о праздниках
/disconnections - Получить информацию об отключениях
/add_group - Добавить группу для оповещений
/request - Оставить запрос или сообщить о проблеме
"""
        await message.answer(help_text)
    
    # Команда /weather - получение погоды
    @dp.message(Command("weather"))
    async def cmd_weather(message: Message):
        weather_data = weather.get_weather()
        if weather_data:
            response = f"Погода в Красноярске:\n\n"
            response += f"Описание: {weather_data['description']}\n"
            response += f"Температура: {weather_data['temperature']}°C\n"
            response += f"Ощущается как: {weather_data['feels_like']}°C\n"
            response += f"Влажность: {weather_data['humidity']}%\n"
            response += f"Скорость ветра: {weather_data['wind_speed']} м/с"
        else:
            response = "Не удалось получить информацию о погоде"
        
        await message.answer(response)
    
    # Команда /holidays - получение праздников
    @dp.message(Command("holidays"))
    async def cmd_holidays(message: Message):
        holidays_data = holidays.get_holidays()
        if holidays_data:
            response = "Праздники на сегодня:\n\n"
            for holiday in holidays_data:
                response += f"• {holiday['name']}\n"
                if holiday['comment']:
                    response += f"  {holiday['comment'][:100]}...\n"
                response += "\n"
        else:
            response = "На сегодня праздников нет"
        
        await message.answer(response)
    
    # Команда /disconnections - получение информации об отключениях
    @dp.message(Command("disconnections"))
    async def cmd_disconnections(message: Message):
        disconnections_data = disconnections.get_disconnections()
        if disconnections_data:
            response = "Отключения на ближайшие дни:\n\n"
            for disconnect in disconnections_data[:5]:  # Показываем первые 5 записей
                response += f"Дата: {disconnect['date'].strftime('%d.%m.%Y %H:%M')}\n"
                response += f"Адрес: {disconnect['address']}\n"
                response += f"Описание: {disconnect['description']}\n\n"
        else:
            response = "Информация об отключениях отсутствует"
        
        await message.answer(response)
    
    # Команда /add_group - добавление группы
    @dp.message(Command("add_group"))
    async def cmd_add_group(message: Message):
        db = next(get_db())
        try:
            # Проверяем, существует ли группа
            group = db.query(Group).filter(Group.group_id == str(message.chat.id)).first()
            if not group:
                # Создаем новую группу
                new_group = Group(
                    group_id=str(message.chat.id),
                    group_name=message.chat.title or "Без названия",
                    is_active=True
                )
                db.add(new_group)
                db.commit()
                await message.answer("Группа успешно добавлена!")
            else:
                await message.answer("Группа уже добавлена!")
        except Exception as e:
            logger.error(f"Ошибка при добавлении группы: {str(e)}")
            await message.answer("Произошла ошибка при добавлении группы")
        finally:
            db.close()