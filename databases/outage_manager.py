from databases.base_manager import BaseManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from databases.models import Outage
import logging
import json
from sqlalchemy import and_, desc
from sqlalchemy.exc import SQLAlchemyError

# Импортируем функцию для генерации хэша
from utils.outage_hash import generate_outage_hash

# Настройка логирования
logger = logging.getLogger(__name__)

class OutageManager(BaseManager):
    """Менеджер для работы с отключениями"""
    
    def add_outages(self, outages_data: List[dict]) -> List[Outage]:
        """Добавление новых отключений"""
        with self.session_manager as session:
            try:
                outages = []
                new_outages_count = 0
                existing_outages_count = 0
                
                for data in outages_data:
                    # Генерируем хэш для проверки дубликатов
                    content_hash = generate_outage_hash(data)
                    
                    # Проверяем, существует ли уже отключение с таким хэшем
                    existing_outage = session.query(Outage).filter(Outage.content_hash == content_hash).first()
                    if existing_outage:
                        logger.info(f"Отключение уже существует в базе данных (хэш: {content_hash[:8]}...)")
                        # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                        _ = existing_outage.id
                        _ = existing_outage.district
                        _ = existing_outage.resource
                        _ = existing_outage.organization
                        _ = existing_outage.phone
                        _ = existing_outage.addresses
                        _ = existing_outage.reason
                        _ = existing_outage.start_time
                        _ = existing_outage.end_time
                        _ = existing_outage.created_at
                        _ = existing_outage.notified
                        _ = existing_outage.content_hash
                        # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                        session.expunge(existing_outage)
                        outages.append(existing_outage)
                        existing_outages_count += 1
                        continue
                    
                    addresses_json = json.dumps(data.get('addresses', []))
                    outage = Outage(
                        district=data.get('district', ''),
                        resource=data.get('resource', ''),
                        organization=data.get('organization', ''),
                        phone=data.get('phone', ''),
                        addresses=addresses_json,
                        reason=data.get('reason', ''),
                        start_time=data.get('start', ''),
                        end_time=data.get('end', ''),
                        content_hash=content_hash
                    )
                    session.add(outage)
                    # Принудительно записываем в БД, но не коммитим транзакцию, чтобы получить ID
                    session.flush()
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = outage.id
                    _ = outage.district
                    _ = outage.resource
                    _ = outage.organization
                    _ = outage.phone
                    _ = outage.addresses
                    _ = outage.reason
                    _ = outage.start_time
                    _ = outage.end_time
                    _ = outage.created_at
                    _ = outage.notified
                    _ = outage.content_hash
                    # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                    session.expunge(outage)
                    outages.append(outage)
                    new_outages_count += 1
                
                logger.info(f"Добавлено {len(outages)} записей об отключениях ({new_outages_count} новых, {existing_outages_count} существующих)")
                return outages
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при добавлении отключений: {e}")
                raise
    
    def get_unnotified_outages(self) -> List[Outage]:
        """Получение нотифицированных отключений"""
        with self.session_manager as session:
            try:
                outages = session.query(Outage).filter(Outage.notified == False).all()
                # Принудительно загружаем атрибуты для каждого отключения и отсоединяем объекты от сессии
                for outage in outages:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = outage.id
                    _ = outage.district
                    _ = outage.resource
                    _ = outage.organization
                    _ = outage.phone
                    _ = outage.addresses
                    _ = outage.reason
                    _ = outage.start_time
                    _ = outage.end_time
                    _ = outage.created_at
                    _ = outage.notified
                    _ = outage.content_hash
                    # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                    session.expunge(outage)
                return outages
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении нотифицированных отключений: {e}")
                raise
    
    
    def get_outages_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Outage]:
        """Получение отключений в заданном диапазоне дат"""
        with self.session_manager as session:
            try:
                outages = session.query(Outage).filter(
                    and_(
                        Outage.created_at >= start_date,
                        Outage.created_at <= end_date
                    )
                ).all()
                # Принудительно загружаем атрибуты для каждого отключения и отсоединяем объекты от сессии
                for outage in outages:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = outage.id
                    _ = outage.district
                    _ = outage.resource
                    _ = outage.organization
                    _ = outage.phone
                    _ = outage.addresses
                    _ = outage.reason
                    _ = outage.start_time
                    _ = outage.end_time
                    _ = outage.created_at
                    _ = outage.notified
                    _ = outage.content_hash
                    # Отсоединяем объект от сессии, чтобы избежать DetachedInstanceError
                    session.expunge(outage)
                return outages
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении отключений в диапазоне дат: {e}")
                raise
    
    def mark_outages_as_notified(self, outage_ids: List[int]) -> bool:
        """Пометить отключения как нотифицированные"""
        with self.session_manager as session:
            try:
                session.query(Outage).filter(Outage.id.in_(outage_ids)).update(
                    {Outage.notified: True}, synchronize_session=False
                )
                logger.info(f"Помечено {len(outage_ids)} отключений как нотифицированные")
                return True
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при пометке отключений как нотифицированных: {e}")
                raise