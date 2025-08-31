"""
Модуль для отправки сообщений через Telegram API
"""
import asyncio
import traceback
import io
import logging
import sys
import os
# Add the databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'databases'))

from aiogram import Bot
from aiogram.types import BufferedInputFile
import databases.config as config

# Настройка логирования
logger = logging.getLogger(__name__)

async def send_message_to_group(group_id: str, message_text: str):
    """
    Отправка сообщения в конкретную группу
    """
    # Создаем новый экземпляр бота для каждой операции
    bot = Bot(token=config.TELEGRAM_TOKEN)
    try:
        await bot.send_message(group_id, message_text)
        logger.info(f"Сообщение успешно отправлено в группу {group_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в группу {group_id}: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return False
    finally:
        # Важно закрыть сессию бота после использования
        await bot.session.close()

async def send_message_with_images_to_group(group_id: str, message_text: str, images):
    """
    Отправка сообщения с изображениями в конкретную группу
    """
    # Создаем новый экземпляр бота для каждой операции
    bot = Bot(token=config.TELEGRAM_TOKEN)
    try:
        # Отправляем текстовое сообщение
        if message_text:
            await bot.send_message(group_id, message_text)
            logger.info(f"Текстовое сообщение отправлено в группу {group_id}")
        
        # Отправляем изображения
        for i, image in enumerate(images):
            # Сбрасываем указатель файла в начало
            image.seek(0)
            # Читаем содержимое файла
            image_data = image.read()
            # Создаем объект BufferedInputFile
            photo = BufferedInputFile(image_data, filename=image.filename or f"image_{i}.jpg")
            # Отправляем изображение
            await bot.send_photo(group_id, photo)
            logger.info(f"Изображение {i+1} отправлено в группу {group_id}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения с изображениями в группу {group_id}: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return False
    finally:
        # Важно закрыть сессию бота после использования
        await bot.session.close()

async def send_message_to_groups(group_ids: list, message_text: str):
    """
    Отправка сообщения в несколько групп
    """
    # Создаем новый экземпляр бота для каждой операции
    bot = Bot(token=config.TELEGRAM_TOKEN)
    try:
        tasks = []
        for group_id in group_ids:
            # Создаем задачу для каждой группы с использованием одного и того же экземпляра бота
            task = bot.send_message(group_id, message_text)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Проверяем, есть ли среди результатов исключения
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Отправлено сообщений в {success_count} групп из {len(group_ids)}")
        return success_count
    except Exception as e:
        logger.error(f"Ошибка отправки сообщений в группы: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return 0
    finally:
        # Важно закрыть сессию бота после использования
        await bot.session.close()

async def send_message_with_images_to_groups(group_ids: list, message_text: str, images):
    """
    Отправка сообщения с изображениями в несколько групп
    """
    # Создаем новый экземпляр бота для каждой операции
    bot = Bot(token=config.TELEGRAM_TOKEN)
    try:
        # Создаем копии изображений для каждой группы
        image_copies = []
        for image in images:
            image.seek(0)
            image_data = image.read()
            image_copy = io.BytesIO(image_data)
            image_copy.filename = image.filename
            image_copies.append(image_copy)
        
        tasks = []
        for group_id in group_ids:
            # Создаем задачу для каждой группы с использованием одного и того же экземпляра бота
            # Отправляем текстовое сообщение
            if message_text:
                tasks.append(bot.send_message(group_id, message_text))
            
            # Отправляем изображения
            for image in image_copies:
                image.seek(0)
                image_data = image.read()
                photo = BufferedInputFile(image_data, filename=image.filename or "image.jpg")
                tasks.append(bot.send_photo(group_id, photo))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Проверяем, есть ли среди результатов исключения
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Отправлено сообщений с изображениями в {success_count} групп из {len(group_ids)}")
        return success_count
    except Exception as e:
        logger.error(f"Ошибка отправки сообщений с изображениями в группы: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return 0
    finally:
        # Важно закрыть сессию бота после использования
        await bot.session.close()

def send_message_sync(group_id: str, message_text: str):
    """
    Синхронная версия отправки сообщения
    """
    try:
        result = asyncio.run(send_message_to_group(group_id, message_text))
        return result > 0  # Если хотя бы одно сообщение отправлено успешно
    except Exception as e:
        logger.error(f"Ошибка синхронной отправки сообщения: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return False

def send_messages_sync(group_ids: list, message_text: str):
    """
    Синхронная версия отправки сообщений в несколько групп
    """
    try:
        sent_count = asyncio.run(send_message_to_groups(group_ids, message_text))
        return sent_count
    except Exception as e:
        logger.error(f"Ошибка синхронной отправки сообщений: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return 0

def send_messages_with_images_sync(group_ids: list, message_text: str, images):
    """
    Синхронная версия отправки сообщений с изображениями в несколько групп
    """
    try:
        # Создаем копии изображений для отправки
        image_copies = []
        for image in images:
            if image and image.filename:
                image.seek(0)
                image_data = image.read()
                image_copy = io.BytesIO(image_data)
                image_copy.filename = image.filename
                image_copies.append(image_copy)
        
        if not image_copies:
            # Если нет изображений, отправляем обычные сообщения
            return send_messages_sync(group_ids, message_text)
        
        sent_count = asyncio.run(send_message_with_images_to_groups(group_ids, message_text, image_copies))
        return sent_count
    except Exception as e:
        logger.error(f"Ошибка синхронной отправки сообщений с изображениями: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        return 0