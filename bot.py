import asyncio
import logging
import threading
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.utils.exceptions import Unauthorized, NetworkError, RetryAfter, TelegramAPIError
from data.config import TELEGRAM_TOKEN
from handlers import register_handlers
from utils.scheduler import scheduler
import schedule
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Флаг для контроля работы шедулера
scheduler_running = True

# Файл-флаг для обновления задач
REFRESH_FLAG_FILE = "scheduler_refresh.flag"

def check_refresh_flag():
    """Проверяет наличие файла-флага и удаляет его"""
    if os.path.exists(REFRESH_FLAG_FILE):
        try:
            os.remove(REFRESH_FLAG_FILE)
            logger.info("Файл-флаг обновления задач обнаружен и удален")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении файла-флага: {e}")
    return False

def clear_schedule():
    """Очищает все запланированные задачи"""
    schedule.clear()
    logger.info("Все запланированные задачи очищены")

def load_scheduled_tasks():
    """Загружает задачи из базы данных"""
    try:
        logger.info("Загрузка задач из базы данных")
        from databases.manager import db_manager
        tasks = db_manager.get_active_scheduled_tasks()
        
        if not tasks:
            logger.info("Нет активных задач в базе данных")
        else:
            logger.info(f"Найдено {len(tasks)} активных задач в базе данных")
            # Загружаем задачи из базы данных
            for task in tasks:
                try:
                    # Создаем функцию для выполнения задачи
                    job_func = lambda t=task: asyncio.run(scheduler.execute_task(t))
                    
                    # Планируем задачу в зависимости от типа интервала
                    if task['interval_type'] == "minute":
                        scheduled_job = schedule.every(task['interval_value']).minutes.do(job_func)
                    elif task['interval_type'] == "hour":
                        scheduled_job = schedule.every(task['interval_value']).hours.do(job_func)
                    elif task['interval_type'] == "day":
                        scheduled_job = schedule.every(task['interval_value']).days.do(job_func)
                    elif task['interval_type'] == "week":
                        scheduled_job = schedule.every(task['interval_value']).weeks.do(job_func)
                    elif task['interval_type'] == "month":
                        # Для месяцев используем приблизительное значение (30 дней)
                        scheduled_job = schedule.every(task['interval_value'] * 30).days.do(job_func)
                    else:
                        logger.warning(f"Неизвестный тип интервала: {task['interval_type']}")
                        continue
                    
                    logger.info(f"Запланирована задача: {task['name']} с типами {task['task_types']} каждые {task['interval_value']} {task['interval_type']}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при планировании задачи {task['name']}: {e}")
        
        logger.info("Загрузка задач завершена")
    except Exception as e:
        logger.error(f"Ошибка при загрузке задач из базы данных: {e}", exc_info=True)

def run_scheduler():
    """Функция для запуска шедулера в отдельном потоке"""
    logger.info("Запуск планировщика задач")
    
    try:
        # Инициализируем типы задач
        from databases.manager import db_manager
        db_manager.initialize_task_types()
        
        # Загружаем задачи при запуске
        load_scheduled_tasks()
        logger.info("Планировщик задач успешно инициализирован")
        
        # Запускаем цикл планировщика
        logger.info("Запуск цикла планировщика")
        iteration_count = 0
        while scheduler_running:
            try:
                iteration_count += 1
                if iteration_count % 10 == 0:  # Log every 10 iterations
                    logger.info(f"Планировщик работает, итерация {iteration_count}")
                
                # Проверяем наличие файла-флага для обновления задач
                if check_refresh_flag():
                    logger.info("Обнаружен файл-флаг обновления задач, перезагружаем задачи")
                    clear_schedule()
                    load_scheduled_tasks()
                
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка в цикле планировщика: {e}", exc_info=True)
                time.sleep(10)  # Ждем 10 секунд перед следующей попыткой
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске планировщика: {e}", exc_info=True)

# Обработчик ошибок
@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    """Глобальный обработчик ошибок"""
    logger.error(f"Произошла ошибка при обработке обновления: {exception}", exc_info=True)
    
    # Обработка специфических ошибок
    if isinstance(exception, Unauthorized):
        logger.error("Бот заблокирован или не авторизован")
    elif isinstance(exception, NetworkError):
        logger.error("Сетевая ошибка при взаимодействии с Telegram API")
    elif isinstance(exception, RetryAfter):
        logger.error(f"Превышен лимит запросов. Повтор через {exception.timeout} секунд")
    elif isinstance(exception, TelegramAPIError):
        logger.error(f"Ошибка Telegram API: {exception}")
    else:
        logger.error(f"Неизвестная ошибка: {type(exception).__name__}: {exception}")
    
    # Отправляем сообщение об ошибке пользователю, если это возможно
    try:
        if update.message:
            await update.message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")
        elif update.callback_query:
            await update.callback_query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об ошибке пользователю: {e}")
    
    return True  # Ошибка обработана

# Регистрация обработчиков
register_handlers(dp)

if __name__ == "__main__":
    logger.info("Запуск Telegram бота")
    try:
        # Запускаем шедулер в отдельном потоке
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Планировщик задач запущен в отдельном потоке")
        
        # Проверяем токен и подключение к Telegram
        bot_info = asyncio.get_event_loop().run_until_complete(bot.get_me())
        logger.info(f"Бот запущен: @{bot_info.username} (ID: {bot_info.id})")
        
        # Запуск бота
        executor.start_polling(dp, skip_updates=True)
    except Unauthorized:
        logger.error("Неверный токен бота. Проверьте TELEGRAM_TOKEN в конфигурации.")
    except NetworkError:
        logger.error("Ошибка сети. Проверьте подключение к интернету.")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
    finally:
        # Останавливаем шедулер при завершении работы
        scheduler_running = False
        if 'scheduler_thread' in locals():
            scheduler_thread.join(timeout=5)
        logger.info("Бот остановлен")