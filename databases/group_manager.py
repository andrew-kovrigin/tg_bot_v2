from databases.base_manager import BaseManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from databases.models import Group
import logging
import json
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logger = logging.getLogger(__name__)

class GroupManager(BaseManager):
    """Менеджер для работы с группами"""
    
    def add_group(self, group_id: str, name: str, addresses: List[str]) -> Group:
        """Добавление новой группы или обновление существующей"""
        with self.session_manager as session:
            try:
                # Проверяем, существует ли уже группа с таким ID
                existing_group = session.query(Group).filter(Group.group_id == group_id).first()
                
                if existing_group:
                    # Если группа существует, обновляем её данные
                    existing_group.name = name
                    existing_group.addresses = json.dumps(addresses)
                    existing_group.is_active = True  # Активируем, если была неактивна
                    session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                    session.refresh(existing_group)  # Обновляем состояние объекта
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = existing_group.id
                    _ = existing_group.group_id
                    _ = existing_group.name
                    _ = existing_group.addresses
                    _ = existing_group.is_active
                    _ = existing_group.created_at
                    logger.info(f"Обновлена существующая группа: {name} ({group_id})")
                    return existing_group
                else:
                    # Если группа не существует, создаем новую
                    addresses_json = json.dumps(addresses)
                    group = Group(group_id=group_id, name=name, addresses=addresses_json)
                    session.add(group)
                    session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                    session.refresh(group)  # Обновляем состояние объекта
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                    logger.info(f"Добавлена новая группа: {name} ({group_id})")
                    return group
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при добавлении/обновлении группы {name} ({group_id}): {e}")
                raise
    
    def get_all_groups(self) -> List[Group]:
        """Получение всех групп"""
        with self.session_manager as session:
            try:
                groups = session.query(Group).filter(Group.is_active == True).all()
                # Принудительно загружаем атрибуты для каждой группы
                for group in groups:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                # Отсоединяем все объекты от сессии после завершения запроса
                for group in groups:
                    session.expunge(group)
                return groups
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении списка групп: {e}")
                raise
    
    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        """Получение группы по ID"""
        with self.session_manager as session:
            try:
                group = session.query(Group).filter(
                    and_(
                        Group.group_id == group_id,
                        Group.is_active == True
                    )
                ).first()
                # If group is found, load all attributes within the current session
                if group:
                    # Force load attributes so they're available after session close
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                    # Отсоединяем объект от сессии после завершения запроса
                    session.expunge(group)
                return group
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении группы {group_id}: {e}")
                raise
    
    def get_groups_by_ids(self, group_ids: List[int]) -> List[Group]:
        """Получение групп по списку ID"""
        with self.session_manager as session:
            try:
                groups = session.query(Group).filter(
                    and_(
                        Group.id.in_(group_ids),
                        Group.is_active == True
                    )
                ).all()
                # Принудительно загружаем атрибуты для каждой группы
                for group in groups:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                return groups
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении групп по списку ID: {e}")
                raise
    
    def update_group_addresses(self, group_id: str, addresses: List[str]) -> bool:
        """Обновление адресов группы"""
        with self.session_manager as session:
            try:
                group = session.query(Group).filter(Group.group_id == group_id).first()
                if group:
                    group.addresses = json.dumps(addresses)
                    logger.info(f"Обновлены адреса группы {group_id}")
                    return True
                logger.warning(f"Группа {group_id} не найдена при обновлении адресов")
                return False
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при обновлении адресов группы {group_id}: {e}")
                raise
    
    def update_group(self, group_id: int, name: str, addresses: List[str]) -> Optional[dict]:
        """Обновление группы"""
        with self.session_manager as session:
            try:
                group = session.query(Group).filter(Group.id == group_id).first()
                if group:
                    group.name = name
                    group.addresses = json.dumps(addresses)
                    session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                    
                    result = {
                        'id': group.id,
                        'group_id': group.group_id,
                        'name': group.name,
                        'addresses': addresses,
                        'is_active': group.is_active,
                        'created_at': group.created_at.isoformat() if group.created_at else None
                    }
                    logger.info(f"Обновлена группа с ID {group_id}")
                    return result
                logger.warning(f"Группа с ID {group_id} не найдена")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при обновлении группы с ID {group_id}: {e}")
                raise
    
    def deactivate_group(self, group_id: int) -> bool:
        """Деактивация группы"""
        with self.session_manager as session:
            try:
                group = session.query(Group).filter(Group.id == group_id).first()
                if group:
                    group.is_active = False
                    logger.info(f"Деактивирована группа с ID {group_id}")
                    return True
                logger.warning(f"Группа с ID {group_id} не найдена")
                return False
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при деактивации группы с ID {group_id}: {e}")
                raise