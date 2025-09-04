from aiogram import Dispatcher
from handlers.user import register_handlers as register_user_handlers

def register_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков"""
    register_user_handlers(dp)