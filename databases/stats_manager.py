from databases.base_manager import BaseManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from databases.models import Group, Outage, Notification
import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logger = logging.getLogger(__name__)

class StatsManager(BaseManager):
    """Менеджер для получения статистики системы"""
    
    def get_system_stats(self) -> dict:
        """Получение статистики системы"""
        with self.session_manager as session:
            try:
                # Получаем количество записей по типам
                groups_count = session.query(func.count(Group.id)).filter(Group.is_active == True).scalar()
                outages_count = session.query(func.count(Outage.id)).scalar()
                notifications_count = session.query(func.count(Notification.id)).scalar()
                
                # Получаем количество уникальных отключений (с непустым content_hash)
                unique_outages_count = session.query(func.count(Outage.id)).filter(Outage.content_hash.isnot(None)).scalar()
                
                # Получаем последние уведомления
                recent_notifications = self._get_recent_notifications(session, limit=5)
                notifications_data = []
                for notification in recent_notifications:
                    notifications_data.append({
                        'id': notification.id,
                        'event_type': notification.event_type,
                        'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
                        'sent_at': notification.sent_at.isoformat() if notification.sent_at else None
                    })
                
                stats = {
                    'counts': {
                        'groups': groups_count,
                        'outages': outages_count,
                        'unique_outages': unique_outages_count,
                        'notifications': notifications_count
                    },
                    'recent_notifications': notifications_data
                }
                logger.info("Получена статистика системы")
                return stats
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении статистики системы: {e}")
                raise
    
    def get_duplicate_stats(self) -> dict:
        """Получение статистики по дубликатам"""
        with self.session_manager as session:
            try:
                # Общее количество отключений
                total_outages = session.query(func.count(Outage.id)).scalar()
                
                # Количество отключений с хэшем (уникальные)
                unique_outages = session.query(func.count(Outage.id)).filter(Outage.content_hash.isnot(None)).scalar()
                
                # Получаем статистику по уведомлениям
                total_notifications = session.query(func.count(Notification.id)).scalar()
                duplicate_notifications = session.query(func.count(Notification.id)).filter(Notification.is_duplicate == True).scalar()
                
                # Рассчитываем процент дубликатов среди уведомлений
                duplicate_percentage = round(duplicate_notifications / total_notifications * 100, 2) if total_notifications > 0 else 0
                
                stats = {
                    'total_outages': total_outages,
                    'unique_outages': unique_outages,
                    'duplicates_prevented': duplicate_notifications,
                    'duplicate_percentage': duplicate_percentage
                }
                
                logger.info("Получена статистика по дубликатам")
                return stats
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении статистики по дубликатам: {e}")
                raise
    
    def _get_recent_notifications(self, session, limit: int = 100) -> List[Notification]:
        """Получение последних уведомлений (внутренний метод)"""
        try:
            from sqlalchemy import desc
            notifications = session.query(Notification).order_by(desc(Notification.sent_at)).limit(limit).all()
            return notifications
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении уведомлений: {e}")
            raise