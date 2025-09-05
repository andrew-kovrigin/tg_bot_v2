from databases.database import DatabaseSessionManager
from databases.models import Base
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class BaseManager:
    """Базовый менеджер для работы с базой данных"""
    
    def __init__(self, engine):
        self.engine = engine
        self.session_manager = DatabaseSessionManager(engine)
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.session_manager.get_session()