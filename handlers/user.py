from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import CommandStart, CommandHelp
from databases.manager import db_manager
import json
import logging
import requests

# Настройка логирования
logger = logging.getLogger(__name__)

async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer("Привет! Я бот для уведомлений об отключениях коммунальных услуг.\n\n"
                         "Используйте /help для получения списка доступных команд.")

async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать помощь\n"
        "/outages - Показать текущие отключения\n"
        "/stats - Показать статистику по отключениям\n"
    )
    await message.answer(help_text)

async def cmd_outages(message: types.Message):
    """Обработчик команды /outages"""
    try:
        # Получаем нотифицированные отключения
        unnotified_outages = db_manager.get_unnotified_outages()
        
        if not unnotified_outages:
            await message.answer("На данный момент нет новых отключений.")
            return
        
        # Формируем сообщение
        response = f"⚠️ *Новые отключения* ({len(unnotified_outages)} шт.):\n\n"
        
        for outage in unnotified_outages[:5]:  # Ограничиваем 5 отключениями
            # Парсим адреса
            try:
                addresses = json.loads(outage.addresses) if outage.addresses else []
                addresses_text = ""
                if addresses:
                    addresses_parts = []
                    for addr in addresses:
                        street = addr.get('street', '')
                        houses = addr.get('houses', [])
                        if houses:
                            addresses_parts.append(f"{street} ({', '.join(houses)})")
                        else:
                            addresses_parts.append(street)
                    addresses_text = "; ".join(addresses_parts)
            except:
                addresses_text = outage.addresses or ""
            
            response += f"🏢 *Район:* {outage.district}\n"
            response += f"💡 *Ресурс:* {outage.resource}\n"
            if outage.organization:
                response += f"🏢 *Организация:* {outage.organization}\n"
            if outage.phone:
                response += f"📞 *Телефон:* {outage.phone}\n"
            if addresses_text:
                response += f"📍 *Адреса:* {addresses_text}\n"
            if outage.reason:
                response += f"📝 *Причина:* {outage.reason}\n"
            if outage.start_time and outage.end_time:
                response += f"⏰ *Время:* {outage.start_time} - {outage.end_time}\n"
            response += "\n"
        
        if len(unnotified_outages) > 5:
            response += f"... и ещё {len(unnotified_outages) - 5} отключений\n\n"
        
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Ошибка при получении отключений: {str(e)}")


async def cmd_stats(message: types.Message):
    """Обработчик команды /stats"""
    try:
        # Получаем последние отключения для статистики
        recent_outages = db_manager.get_recent_outages(100)
        
        if not recent_outages:
            await message.answer("На данный момент нет данных для статистики.")
            return
        
        # Собираем статистику
        total_outages = len(recent_outages)
        resources = {}
        districts = {}
        
        for outage in recent_outages:
            # Статистика по ресурсам
            resource = outage.resource or "Не указан"
            resources[resource] = resources.get(resource, 0) + 1
            
            # Статистика по районам
            district = outage.district or "Не указан"
            districts[district] = districts.get(district, 0) + 1
        
        # Формируем сообщение
        response = "📊 *Статистика отключений:*\n\n"
        response += f"📈 *Всего отключений:* {total_outages}\n\n"
        
        response += "💡 *По ресурсам:*\n"
        for resource, count in sorted(resources.items(), key=lambda x: x[1], reverse=True)[:5]:
            response += f"  {resource}: {count}\n"
        
        response += "\n🏢 *По районам:*\n"
        for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True)[:5]:
            response += f"  {district}: {count}\n"
        
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Ошибка при получении статистики: {str(e)}")

async def cmd_recent(message: types.Message):
   """Обработчик команды /recent"""
   try:
       # Получаем последние отключения (не обязательно нотифицированные)
       recent_outages = db_manager.get_recent_outages(10)  # Получаем последние 10 отключений
       
       if not recent_outages:
           await message.answer("На данный момент нет недавних отключений.")
           return
       
       # Формируем сообщение
       response = f"🕒 *Последние отключения* ({len(recent_outages)} шт.):\n\n"
       
       for outage in recent_outages:
           # Парсим адреса
           try:
               addresses = json.loads(outage.addresses) if outage.addresses else []
               addresses_text = ""
               if addresses:
                   addresses_parts = []
                   for addr in addresses:
                       street = addr.get('street', '')
                       houses = addr.get('houses', [])
                       if houses:
                           addresses_parts.append(f"{street} ({', '.join(houses)})")
                       else:
                           addresses_parts.append(street)
                   addresses_text = "; ".join(addresses_parts)
           except:
               addresses_text = outage.addresses or ""
           
           response += f"🏢 *Район:* {outage.district}\n"
           response += f"💡 *Ресурс:* {outage.resource}\n"
           if outage.organization:
               response += f"🏢 *Организация:* {outage.organization}\n"
           if outage.phone:
               response += f"📞 *Телефон:* {outage.phone}\n"
           if addresses_text:
               response += f"📍 *Адреса:* {addresses_text}\n"
           if outage.reason:
               response += f"📝 *Причина:* {outage.reason}\n"
           if outage.start_time and outage.end_time:
               response += f"⏰ *Время:* {outage.start_time} - {outage.end_time}\n"
           response += "\n"
       
       await message.answer(response, parse_mode="Markdown")
   except Exception as e:
       await message.answer(f"Ошибка при получении последних отключений: {str(e)}")

async def on_bot_added_to_group(message: types.Message):
    """Обработчик события добавления бота в группу"""
    try:
        # Проверяем, что это сообщение о добавлении бота в группу
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == (await message.bot.get_me()).id:
                    # Бот добавлен в группу
                    chat_id = message.chat.id
                    chat_title = message.chat.title or f"Группа {chat_id}"
                    
                    logger.info(f"Бот добавлен в группу: {chat_title} (ID: {chat_id})")
                    
                    # Отправляем уведомление в группу
                    await message.answer(
                        f"Привет! Я бот для уведомлений об отключениях коммунальных услуг.\n"
                        f"Группа '{chat_title}' (ID: {chat_id}) успешно зарегистрирована.\n\n"
                        f"Для настройки фильтрации по адресам обратитесь к администратору через веб-панель."
                    )
                    
                    # Отправляем информацию в админку для автоматического добавления группы
                    try:
                        from data.config import ADMIN_PANEL_URL
                        admin_url = ADMIN_PANEL_URL or "http://localhost:5000"
                        response = requests.post(
                            f"{admin_url}/api/add_group_from_telegram",
                            json={
                                "group_id": str(chat_id),
                                "name": chat_title,
                                "addresses": []
                            },
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            logger.info(f"Группа {chat_title} успешно добавлена в базу данных")
                        else:
                            logger.error(f"Ошибка при добавлении группы в базу данных: {response.text}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке данных в админку: {e}")
                    
                    break
    except Exception as e:
        logger.error(f"Ошибка при обработке добавления бота в группу: {e}")

def register_handlers(dp: Dispatcher):
    """Регистрация обработчиков"""
    dp.register_message_handler(cmd_start, CommandStart())
    dp.register_message_handler(cmd_help, CommandHelp())
    dp.register_message_handler(cmd_outages, commands=["outages"])
    dp.register_message_handler(cmd_stats, commands=["stats"])
    # Обработчик для события добавления бота в группу
    dp.register_message_handler(on_bot_added_to_group, content_types=[types.ContentType.NEW_CHAT_MEMBERS])