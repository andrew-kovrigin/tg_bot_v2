#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Request handling functionality
"""
import logging
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from databases.models import UserRequest, get_db

logger = logging.getLogger(__name__)

# Определение состояний для FSM
class RequestStates(StatesGroup):
    waiting_for_request = State()

def register_request_handlers(dp, RequestStates):
    """Register request handlers"""
    
    # Команда /request - оставить запрос
    @dp.message(Command("request"))
    async def cmd_request(message: Message, state: FSMContext):
        await message.answer("Пожалуйста, опишите ваш запрос или проблему, и я передам её администраторам.")
        # Устанавливаем состояние ожидания текста запроса
        await state.set_state(RequestStates.waiting_for_request)
    
    # Обработчик текстовых сообщений для запросов
    @dp.message(RequestStates.waiting_for_request)
    async def handle_request_text(message: Message, state: FSMContext):
        # Создаем запрос в базе данных
        db = next(get_db())
        try:
            new_request = UserRequest(
                user_id=message.from_user.id,
                username=message.from_user.username,
                group_id=str(message.chat.id) if message.chat else None,
                message_text=message.text
            )
            db.add(new_request)
            db.commit()
            await message.answer("Ваш запрос успешно отправлен администраторам. Спасибо!")
        except Exception as e:
            logger.error(f"Ошибка при создании запроса: {str(e)}")
            await message.answer("Произошла ошибка при отправке запроса. Попробуйте позже.")
        finally:
            db.close()
        
        # Сбрасываем состояние
        await state.clear()
    
    # Обработчик для всех остальных сообщений
    @dp.message()
    async def handle_other_messages(message: Message):
        # Просто игнорируем сообщения, которые не являются командами и не находятся в состоянии запроса
        pass