import sys
import os

# Добавляем текущую директорию в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from databases.models import Base
from data.config import DATABASE_URL
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

def create_database():
    """Создание базы данных и таблиц"""
    try:
        # Для SQLite добавляем параметры для лучшей производительности
        if DATABASE_URL.startswith('sqlite'):
            engine = create_engine(
                DATABASE_URL, 
                echo=False,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                }
            )
        else:
            engine = create_engine(DATABASE_URL, echo=False)
        
        # Создаем все таблицы
        Base.metadata.create_all(engine)
        
        # Проверяем существование индексов и создаем их при необходимости
        # Это нужно для случаев, когда индексы были добавлены после создания таблиц
        # В production среде лучше использовать миграции
        
        logger.info("База данных и таблицы успешно созданы")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при создании базы данных: {e}")
        raise

def get_session_factory(engine):
    """Получение фабрики сессий"""
    return sessionmaker(bind=engine)

def get_scoped_session(engine):
    """Получение scoped session для веб-приложения"""
    session_factory = get_session_factory(engine)
    return scoped_session(session_factory)

class DatabaseSessionManager:
    """Менеджер сессий базы данных с контекстным менеджером"""
    
    def __init__(self, engine):
        self.engine = engine
        self.session_factory = get_session_factory(engine)
        self.scoped_session = get_scoped_session(engine)
    
    def get_session(self):
        """Получение новой сессии"""
        return self.session_factory()
    
    def get_scoped_session(self):
        """Получение scoped session"""
        return self.scoped_session()
    
    def remove_scoped_session(self):
        """Удаление scoped session (для очистки после запроса)"""
        self.scoped_session.remove()
    
    def __enter__(self):
        """Вход в контекстный менеджер"""
        self.session = self.session_factory()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера"""
        try:
            if exc_type is not None:
                # Если возникло исключение, откатываем транзакцию
                try:
                    self.session.rollback()
                    logger.warning(f"Транзакция откачена из-за исключения: {exc_val}")
                except Exception as rollback_error:
                    logger.error(f"Ошибка при откате транзакции: {rollback_error}")
            else:
                # Если исключения не было, коммитим транзакцию
                # Проверяем, что сессия еще не закрыта и не находится в процессе завершения
                try:
                    # Проверяем состояние сессии перед коммитом
                    if hasattr(self.session, 'is_active') and self.session.is_active:
                        # Проверяем, есть ли незавершенные транзакции
                        if not hasattr(self.session, '_transaction') or self.session._transaction is None or \
                           (hasattr(self.session._transaction, 'is_active') and self.session._transaction.is_active):
                            self.session.commit()
                        else:
                            logger.debug("Нет активной транзакции для коммита")
                    else:
                        logger.debug("Сессия уже неактивна, коммит пропущен")
                except SQLAlchemyError as commit_error:
                    logger.error(f"Ошибка при коммите транзакции: {commit_error}")
                    try:
                        self.session.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Ошибка при откате транзакции: {rollback_error}")
                    raise
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при завершении сессии: {e}")
            try:
                if hasattr(self.session, 'is_active') and self.session.is_active:
                    self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Ошибка при откате транзакции: {rollback_error}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при завершении сессии: {e}")
            try:
                if hasattr(self.session, 'is_active') and self.session.is_active:
                    self.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Ошибка при откате транзакции: {rollback_error}")
            raise
        finally:
            # Всегда закрываем сессию
            try:
                self.session.close()
            except Exception as close_error:
                logger.warning(f"Ошибка при закрытии сессии: {close_error}")
        
        return False  # Не подавляем исключения

if __name__ == "__main__":
    try:
        engine = create_database()
        print("База данных и таблицы успешно созданы!")
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")