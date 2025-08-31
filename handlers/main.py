#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main bot initialization and startup
"""
import asyncio
import logging
import os
import sys
import traceback

# Add the parent directory and databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'databases'))

from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
from sqlalchemy.orm import Session
from databases.models import Group, Admin, UserRequest, SchedulerSettings, get_db
import databases.config as config
import weather
import holidays
import disconnections
from handlers.commands import register_command_handlers
from handlers.requests import RequestStates, register_request_handlers
from handlers.message_sender import send_scheduled_message

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Глобальная переменная для хранения ID задач планировщика
scheduler_jobs = {}

def register_handlers():
    """Register all handlers"""
    register_command_handlers(dp, bot)
    register_request_handlers(dp, RequestStates)

# Функция отправки ежедневного сообщения
async def send_daily_message():
    await send_scheduled_message(bot, "daily_message")

# Функция отправки отчета о погоде
async def send_weather_report():
    await send_scheduled_message(bot, "weather")

# Функция отправки отчета о праздниках
async def send_holidays_report():
    await send_scheduled_message(bot, "holidays")

# Функция отправки отчета об отключениях
async def send_disconnections_report():
    await send_scheduled_message(bot, "disconnections")

# Функция для обновления задач планировщика
async def update_scheduler_jobs():
    global scheduler_jobs
    
    logger.info("Обновление задач планировщика")
    
    # Останавливаем планировщик
    if scheduler.running:
        scheduler.shutdown()
    
    # Очищаем словарь задач
    scheduler_jobs.clear()
    
    # Инициализируем настройки планировщика
    db = next(get_db())
    try:
        # Добавляем задачи для планировщика
        jobs = db.query(SchedulerSettings).filter(SchedulerSettings.is_enabled == True).all()
        
        for job in jobs:
            logger.info(f"Настраиваем задачу: {job.job_name}, тип: {job.job_type}, интервал: {job.interval_type}, значение: {job.interval_value}")
            
            # Определяем функцию для задачи
            if job.job_type == "daily_message":
                job_func = send_daily_message
            elif job.job_type == "weather":
                job_func = send_weather_report
            elif job.job_type == "holidays":
                job_func = send_holidays_report
            elif job.job_type == "disconnections":
                job_func = send_disconnections_report
            else:
                logger.warning(f"Неизвестный тип задачи: {job.job_type}")
                continue  # Неизвестный тип задачи
            
            # Добавляем задачу в планировщик в зависимости от типа интервала
            try:
                job_id = None
                if job.interval_type == "minutely":
                    # Ежеминутные задачи (с интервалом)
                    interval_value = max(1, job.interval_value or 1)
                    job_id = scheduler.add_job(job_func, 'interval', minutes=interval_value).id
                    logger.info(f"Планировщик настроен: {job.job_name} ({job.job_type}) каждые {interval_value} минут")
                elif job.interval_type == "hourly":
                    # Ежечасные задачи (с интервалом)
                    interval_value = max(1, job.interval_value or 1)
                    job_id = scheduler.add_job(job_func, 'interval', hours=interval_value).id
                    logger.info(f"Планировщик настроен: {job.job_name} ({job.job_type}) каждые {interval_value} часов")
                elif job.interval_type == "weekly" and job.day_of_week:
                    # Для еженедельных задач
                    days = job.day_of_week.split(',')
                    for day in days:
                        job_id = scheduler.add_job(job_func, 'cron', day_of_week=int(day), hour=job.hour or 0, minute=job.minute or 0).id
                    logger.info(f"Планировщик настроен: {job.job_name} ({job.job_type}) в {job.hour or 0:02d}:{job.minute or 0:02d} по дням: {job.day_of_week}")
                elif job.interval_type == "monthly" and job.day_of_month:
                    # Для ежемесячных задач
                    job_id = scheduler.add_job(job_func, 'cron', day=job.day_of_month, hour=job.hour or 0, minute=job.minute or 0).id
                    logger.info(f"Планировщик настроен: {job.job_name} ({job.job_type}) в {job.hour or 0:02d}:{job.minute or 0:02d} числа {job.day_of_month}")
                elif job.interval_type == "daily":
                    # Ежедневные задачи
                    job_id = scheduler.add_job(job_func, 'cron', hour=job.hour or 0, minute=job.minute or 0).id
                    logger.info(f"Планировщик настроен: {job.job_name} ({job.job_type}) в {job.hour or 0:02d}:{job.minute or 0:02d} ежедневно")
                else:
                    logger.info(f"Задача {job.job_name} не настроена (некорректные параметры)")
                
                # Сохраняем ID задачи
                if job_id:
                    scheduler_jobs[job.job_name] = job_id
                    
            except Exception as e:
                logger.error(f"Ошибка при настройке задачи {job.job_name}: {str(e)}")
                logger.error(f"Трассировка стека: {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Ошибка при инициализации настроек планировщика: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
    finally:
        db.close()
    
    # Запускаем планировщик
    scheduler.start()
    logger.info("Планировщик обновлен и запущен")

# Функция для проверки файла-флага и обновления планировщика
async def scheduler_watcher():
    """Проверяет наличие файла-флага и обновляет планировщик при необходимости"""
    while True:
        if os.path.exists(config.SCHEDULER_FLAG_FILE):
            logger.info("Обнаружен файл-флаг обновления планировщика")
            try:
                # Удаляем файл-флаг
                os.remove(config.SCHEDULER_FLAG_FILE)
                
                # Обновляем задачи планировщика
                await update_scheduler_jobs()
                
                logger.info("Планировщик успешно обновлен")
            except Exception as e:
                logger.error(f"Ошибка при обновлении планировщика: {str(e)}")
                logger.error(f"Трассировка стека: {traceback.format_exc()}")
        
        # Ждем 5 секунд перед следующей проверкой
        await asyncio.sleep(5)

# Запуск бота
async def main():
    # Регистрация обработчиков
    register_handlers()
    
    # Инициализируем настройки планировщика
    db = next(get_db())
    try:
        # Проверяем и создаем настройки по умолчанию
        default_jobs = [
            {
                "job_name": "daily_message",
                "job_type": "daily_message",
                "is_enabled": True,
                "hour": 7,
                "minute": 0,
                "interval_type": "daily",
                "interval_value": 1,
                "description": "Ежедневное оповещение в 7:00"
            },
            {
                "job_name": "weather_report",
                "job_type": "weather",
                "is_enabled": True,
                "hour": 8,
                "minute": 0,
                "interval_type": "daily",
                "interval_value": 1,
                "description": "Отчет о погоде в 8:00"
            },
            {
                "job_name": "holidays_report",
                "job_type": "holidays",
                "is_enabled": True,
                "hour": 9,
                "minute": 0,
                "interval_type": "daily",
                "interval_value": 1,
                "description": "Отчет о праздниках в 9:00"
            },
            {
                "job_name": "disconnections_report",
                "job_type": "disconnections",
                "is_enabled": True,
                "hour": 10,
                "minute": 0,
                "interval_type": "daily",
                "interval_value": 1,
                "description": "Отчет об отключениях в 10:00"
            },
            {
                "job_name": "hourly_check",
                "job_type": "daily_message",
                "is_enabled": False,
                "hour": None,
                "minute": None,
                "interval_type": "hourly",
                "interval_value": 1,
                "description": "Ежечасная проверка"
            },
            {
                "job_name": "every_30_minutes",
                "job_type": "weather",
                "is_enabled": False,
                "hour": None,
                "minute": None,
                "interval_type": "minutely",
                "interval_value": 30,
                "description": "Проверка каждые 30 минут"
            }
        ]
        
        for job_data in default_jobs:
            existing_job = db.query(SchedulerSettings).filter(
                SchedulerSettings.job_name == job_data["job_name"]
            ).first()
            
            if not existing_job:
                scheduler_setting = SchedulerSettings(**job_data)
                db.add(scheduler_setting)
        
        db.commit()
    except Exception as e:
        logger.error(f"Ошибка при инициализации настроек планировщика: {str(e)}")
        import traceback
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
    finally:
        db.close()
    
    # Обновляем задачи планировщика
    await update_scheduler_jobs()
    
    # Запускаем watcher в фоновом режиме
    asyncio.create_task(scheduler_watcher())
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())