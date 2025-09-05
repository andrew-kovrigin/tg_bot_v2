from databases.base_manager import BaseManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from databases.models import Notification
import logging
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logger = logging.getLogger(__name__)

class NotificationManager(BaseManager):
    """Менеджер для работы с уведомлениями"""
    
    def add_notification(self, event_type: str, event_id: int, group_id: str, message: str, is_duplicate: bool = False) -> Notification:
        """Добавление записи об уведомлении"""
        with self.session_manager as session:
            try:
                notification = Notification(
                    event_type=event_type,
                    event_id=event_id,
                    group_id=group_id,
                    message=message,
                    is_duplicate=is_duplicate
                )
                session.add(notification)
                session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                _ = notification.id
                _ = notification.event_type
                _ = notification.event_id
                _ = notification.group_id
                _ = notification.message
                _ = notification.sent_at
                _ = notification.is_duplicate
                # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                session.expunge(notification)
                logger.info(f"Добавлено уведомление типа {event_type} для группы {group_id}")
                return notification
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при добавлении уведомления: {e}")
                raise
    
    def get_notifications(self, limit: int = 100) -> List[Notification]:
        """Получение последних уведомлений"""
        with self.session_manager as session:
            try:
                notifications = session.query(Notification).order_by(desc(Notification.sent_at)).limit(limit).all()
                # Принудительно загружаем атрибуты для каждого уведомления и отсоединяем объекты от сессии
                for notification in notifications:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = notification.id
                    _ = notification.event_type
                    _ = notification.event_id
                    _ = notification.group_id
                    _ = notification.message
                    _ = notification.sent_at
                    _ = notification.is_duplicate
                    # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                    session.expunge(notification)
                logger.info(f"Получено {len(notifications)} последних уведомлений")
                return notifications
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении уведомлений: {e}")
                raise
    
    def get_notifications_by_type(self, event_type: str, limit: int = 100) -> List[Notification]:
        """Получение уведомлений по типу события"""
        with self.session_manager as session:
            try:
                notifications = session.query(Notification).filter(Notification.event_type == event_type).order_by(desc(Notification.sent_at)).limit(limit).all()
                # Принудительно загружаем атрибуты для каждого уведомления и отсоединяем объекты от сессии
                for notification in notifications:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = notification.id
                    _ = notification.event_type
                    _ = notification.event_id
                    _ = notification.group_id
                    _ = notification.message
                    _ = notification.sent_at
                    _ = notification.is_duplicate
                    # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                    session.expunge(notification)
                logger.info(f"Получено {len(notifications)} уведомлений типа {event_type}")
                return notifications
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении уведомлений типа {event_type}: {e}")
                raise
    
    def get_notification_by_id(self, notification_id: int) -> Optional[Notification]:
        """Получение уведомления по ID"""
        with self.session_manager as session:
            try:
                notification = session.query(Notification).filter(Notification.id == notification_id).first()
                if notification:
                    # Force load attributes so they're available after session close
                    _ = notification.id
                    _ = notification.event_type
                    _ = notification.event_id
                    _ = notification.group_id
                    _ = notification.message
                    _ = notification.sent_at
                    _ = notification.is_duplicate
                    logger.info(f"Получено уведомление с ID {notification_id}")
                    # Отсоединяем объект от сессии после завершения запроса
                    session.expunge(notification)
                else:
                    logger.warning(f"Уведомление с ID {notification_id} не найдено")
                return notification
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении уведомления с ID {notification_id}: {e}")
                raise
    
    def get_notifications_by_group(self, group_id: str, limit: int = 100) -> List[Notification]:
        """Получение уведомлений по ID группы"""
        with self.session_manager as session:
            try:
                notifications = session.query(Notification).filter(Notification.group_id == group_id).order_by(desc(Notification.sent_at)).limit(limit).all()
                # Принудительно загружаем атрибуты для каждого уведомления и отсоединяем объекты от сессии
                for notification in notifications:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = notification.id
                    _ = notification.event_type
                    _ = notification.event_id
                    _ = notification.group_id
                    _ = notification.message
                    _ = notification.sent_at
                    _ = notification.is_duplicate
                    # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                    session.expunge(notification)
                logger.info(f"Получено {len(notifications)} уведомлений для группы {group_id}")
                return notifications
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении уведомлений для группы {group_id}: {e}")
                raise