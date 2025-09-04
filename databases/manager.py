from databases.database import create_database, DatabaseSessionManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .models import Base, Admin, Group, Outage, ScheduledTask, Notification, TaskTypeDefinition
import logging
import json
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError

# Импортируем функцию для генерации хэша
from utils.outage_hash import generate_outage_hash

# Настройка логирования
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.engine = create_database()
        self.session_manager = DatabaseSessionManager(self.engine)
    
    def get_session(self) -> Session:
        """Получение сессии базы данных"""
        return self.session_manager.get_session()
    
    # Методы для работы с администраторами
    def add_admin(self, username: str, password_hash: str) -> Admin:
        """Добавление нового администратора"""
        with self.session_manager as session:
            try:
                admin = Admin(username=username, password_hash=password_hash)
                session.add(admin)
                session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                _ = admin.id
                _ = admin.username
                _ = admin.password_hash
                _ = admin.created_at
                # Отсоединяем объект от сессии
                session.expunge(admin)
                logger.info(f"Добавлен новый администратор: {username}")
                return admin
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при добавлении администратора {username}: {e}")
                raise
    
    def get_admin_by_username(self, username: str) -> Optional[Admin]:
        """Получение администратора по имени пользователя"""
        with self.session_manager as session:
            try:
                admin = session.query(Admin).filter(Admin.username == username).first()
                # Если администратор найден, загружаем все атрибуты в рамках текущей сессии
                if admin:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = admin.id
                    _ = admin.username
                    _ = admin.password_hash
                    _ = admin.created_at
                    # Отсоединяем объект от сессии
                    session.expunge(admin)
                return admin
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении администратора {username}: {e}")
                raise
    
    def get_all_admins(self) -> List[Admin]:
        """Получение всех администраторов"""
        with self.session_manager as session:
            try:
                admins = session.query(Admin).all()
                # Принудительно загружаем атрибуты для каждого администратора
                for admin in admins:
                    _ = admin.id
                    _ = admin.username
                    _ = admin.password_hash
                    _ = admin.created_at
                    # Отсоединяем объект от сессии
                    session.expunge(admin)
                return admins
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении списка администраторов: {e}")
                raise
    
    def delete_admin(self, admin_id: int) -> bool:
        """Удаление администратора"""
        with self.session_manager as session:
            try:
                admin = session.query(Admin).filter(Admin.id == admin_id).first()
                if not admin:
                    logger.warning(f"Администратор с ID {admin_id} не найден")
                    return False
                
                # Не позволяем удалять последнего администратора
                admins_count = session.query(Admin).count()
                if admins_count <= 1:
                    logger.warning("Попытка удаления последнего администратора")
                    return False
                
                session.delete(admin)
                logger.info(f"Администратор с ID {admin_id} удален")
                return True
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при удалении администратора с ID {admin_id}: {e}")
                raise
    
    # Методы для работы с группами
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
                    session.commit()  # Коммитим транзакцию
                    session.refresh(existing_group)  # Обновляем состояние объекта
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = existing_group.id
                    _ = existing_group.group_id
                    _ = existing_group.name
                    _ = existing_group.addresses
                    _ = existing_group.is_active
                    _ = existing_group.created_at
                    # Отсоединяем объект от сессии
                    session.expunge(existing_group)
                    logger.info(f"Обновлена существующая группа: {name} ({group_id})")
                    return existing_group
                else:
                    # Если группа не существует, создаем новую
                    addresses_json = json.dumps(addresses)
                    group = Group(group_id=group_id, name=name, addresses=addresses_json)
                    session.add(group)
                    session.commit()  # Коммитим транзакцию
                    session.refresh(group)  # Обновляем состояние объекта
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                    # Отсоединяем объект от сессии
                    session.expunge(group)
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
                result = []
                for group in groups:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                    # Отсоединяем объект от сессии
                    session.expunge(group)
                    result.append(group)
                return result
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
                    # Expunge the object from the session
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
                result = []
                for group in groups:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = group.id
                    _ = group.group_id
                    _ = group.name
                    _ = group.addresses
                    _ = group.is_active
                    _ = group.created_at
                    # Отсоединяем объект от сессии
                    session.expunge(group)
                    result.append(group)
                return result
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
    
    # Методы для работы с отключениями
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
                        # Отсоединяем объект от сессии
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
                    # Отсоединяем объект от сессии
                    session.expunge(outage)
                    outages.append(outage)
                    new_outages_count += 1
                
                # Принудительно записываем в БД, но не коммитим транзакцию, чтобы получить ID
                session.flush()
                
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
                # Принудительно загружаем атрибуты для каждого отключения
                result = []
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
                    # Отсоединяем объект от сессии
                    session.expunge(outage)
                    result.append(outage)
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении нотифицированных отключений: {e}")
                raise
    
    def get_recent_outages(self, limit: int = 50) -> List[Outage]:
        """Получение последних отключений"""
        with self.session_manager as session:
            try:
                outages = session.query(Outage).order_by(desc(Outage.created_at)).limit(limit).all()
                # Принудительно загружаем атрибуты для каждого отключения
                result = []
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
                    # Отсоединяем объект от сессии
                    session.expunge(outage)
                    result.append(outage)
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении последних отключений: {e}")
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
                # Принудительно загружаем атрибуты для каждого отключения
                result = []
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
                    # Отсоединяем объект от сессии
                    session.expunge(outage)
                    result.append(outage)
                return result
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
    
    # Методы для работы с запланированными задачами
    def add_scheduled_task(self, name: str, task_type_names: List[str], interval_type: str, 
                          interval_value: int, time_of_day: str = None, group_ids: List[int] = None) -> dict:
        """Добавление запланированной задачи"""
        with self.session_manager as session:
            try:
                task = ScheduledTask(
                    name=name,
                    interval_type=interval_type,
                    interval_value=interval_value,
                    time_of_day=time_of_day
                )
                session.add(task)
                session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                
                # Если указаны типы задач, добавляем связи
                assigned_task_type_ids = []
                if task_type_names:
                    task_types = session.query(TaskTypeDefinition).filter(TaskTypeDefinition.name.in_(task_type_names)).all()
                    task.task_types = task_types
                    assigned_task_type_ids = [task_type.id for task_type in task_types]
                
                # Если указаны группы, добавляем связи
                assigned_group_ids = []
                if group_ids:
                    groups = session.query(Group).filter(
                        and_(
                            Group.id.in_(group_ids),
                            Group.is_active == True
                        )
                    ).all()
                    task.groups = groups
                    assigned_group_ids = [group.id for group in groups]
                
                # Возвращаем данные задачи виде словаря, чтобы избежать проблем с сессией
                result = {
                    'id': task.id,
                    'name': task.name,
                    'task_types': assigned_task_type_ids, # ID назначенных типов задач
                    'interval_type': task.interval_type,
                    'interval_value': task.interval_value,
                    'time_of_day': task.time_of_day,
                    'is_active': task.is_active,
                    'assigned_groups': assigned_group_ids,
                    'last_run': task.last_run,
                    'created_at': task.created_at
                }
                
                logger.info(f"Добавлена новая задача: {name}")
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при добавлении задачи {name}: {e}")
                raise
    
    def get_all_scheduled_tasks(self) -> List[dict]:
        """Получение всех запланированных задач"""
        with self.session_manager as session:
            try:
                tasks = session.query(ScheduledTask).all()
                result = []
                for task in tasks:
                    # Загружаем связанные данные в рамках той же сессии
                    assigned_group_ids = [group.id for group in task.groups] if hasattr(task, 'groups') else []
                    assigned_task_type_ids = [task_type.id for task_type in task.task_types] if hasattr(task, 'task_types') else []
                    
                    task_data = {
                        'id': task.id,
                        'name': task.name,
                        'task_types': assigned_task_type_ids,
                        'interval_type': task.interval_type,
                        'interval_value': task.interval_value,
                        'time_of_day': task.time_of_day,
                        'is_active': task.is_active,
                        'assigned_groups': assigned_group_ids,
                        'last_run': task.last_run,
                        'created_at': task.created_at
                    }
                    result.append(task_data)
                logger.info(f"Получено {len(result)} задач")
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении всех задач: {e}")
                raise
    
    def get_active_scheduled_tasks(self) -> List[dict]:
        """Получение активных запланированных задач"""
        with self.session_manager as session:
            try:
                tasks = session.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
                result = []
                for task in tasks:
                    # Загружаем связанные данные в рамках той же сессии
                    assigned_group_ids = [group.id for group in task.groups] if hasattr(task, 'groups') else []
                    assigned_task_type_ids = [task_type.id for task_type in task.task_types] if hasattr(task, 'task_types') else []
                    
                    task_data = {
                        'id': task.id,
                        'name': task.name,
                        'task_types': assigned_task_type_ids,
                        'interval_type': task.interval_type,
                        'interval_value': task.interval_value,
                        'time_of_day': task.time_of_day,
                        'is_active': task.is_active,
                        'assigned_groups': assigned_group_ids,
                        'last_run': task.last_run,
                        'created_at': task.created_at
                    }
                    result.append(task_data)
                logger.info(f"Получено {len(result)} активных задач")
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении активных задач: {e}")
                raise
    
    def get_task_type_by_id(self, type_id: int) -> TaskTypeDefinition:
        """Получение типа задачи по ID"""
        with self.session_manager as session:
            try:
                task_type = session.query(TaskTypeDefinition).filter(TaskTypeDefinition.id == type_id).first()
                # If task type is found, load all attributes within the current session
                if task_type:
                    # Force load attributes so they're available after session close
                    _ = task_type.id
                    _ = task_type.name
                    _ = task_type.display_name
                    _ = task_type.description
                    # Expunge the object from the session
                    session.expunge(task_type)
                return task_type
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении типа задачи с ID {type_id}: {e}")
                raise
    
    def get_all_task_types(self) -> List[TaskTypeDefinition]:
        """Получение всех типов задач"""
        with self.session_manager as session:
            try:
                task_types = session.query(TaskTypeDefinition).all()
                # Принудительно загружаем атрибуты для каждого типа задачи
                result = []
                for task_type in task_types:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = task_type.id
                    _ = task_type.name
                    _ = task_type.display_name
                    _ = task_type.description
                    # Отсоединяем объект от сессии
                    session.expunge(task_type)
                    result.append(task_type)
                return result
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении всех типов задач: {e}")
                raise
    
    def initialize_task_types(self):
        """Инициализация стандартных типов задач"""
        with self.session_manager as session:
            try:
                # Создаем список всех необходимых типов задач
                required_types = [
                    {
                        'name': 'outages_check',
                        'display_name': 'Проверка отключений',
                        'description': 'Проверка текущих отключений коммунальных услуг'
                    }
                ]
                
                # Получаем все существующие типы задач
                existing_types = session.query(TaskTypeDefinition).all()
                existing_names = {t.name for t in existing_types}
                
                # Добавляем те типы, которых еще нет
                added_count = 0
                for type_data in required_types:
                    if type_data['name'] not in existing_names:
                        task_type = TaskTypeDefinition(**type_data)
                        session.add(task_type)
                        added_count += 1
                        logger.info(f"Добавлен тип задачи: {type_data['name']}")
                
                if added_count > 0:
                    logger.info(f"Добавлено {added_count} новых типов задач")
                else:
                    logger.info("Все типы задач уже существуют")
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при инициализации типов задач: {e}")
                raise
    
    def get_task_groups(self, task_id: int) -> List[Group]:
        """Получение групп, связанных с задачей"""
        with self.session_manager as session:
            try:
                task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if task:
                    # Загружаем связанные группы
                    session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                    logger.info(f"Получено {len(task.groups)} групп для задачи с ID {task_id}")
                    # Принудительно загружаем атрибуты для каждой группы
                    result = []
                    for group in task.groups:
                        # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                        _ = group.id
                        _ = group.group_id
                        _ = group.name
                        _ = group.addresses
                        _ = group.is_active
                        _ = group.created_at
                        # Отсоединяем объект от сессии
                        session.expunge(group)
                        result.append(group)
                    return result
                logger.warning(f"Задача с ID {task_id} не найдена")
                return []
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении групп для задачи с ID {task_id}: {e}")
                raise
    
    def deactivate_scheduled_task(self, task_id: int) -> bool:
        """Деактивация запланированной задачи"""
        with self.session_manager as session:
            try:
                task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if task:
                    task.is_active = False
                    logger.info(f"Деактивирована задача с ID {task_id}")
                    return True
                logger.warning(f"Задача с ID {task_id} не найдена")
                return False
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при деактивации задачи с ID {task_id}: {e}")
                raise
    
    def update_scheduled_task(self, task_id: int, name: str, task_type_names: List[str], 
                             interval_type: str, interval_value: int, time_of_day: str = None) -> Optional[dict]:
        """Обновление запланированной задачи"""
        with self.session_manager as session:
            try:
                task = session.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
                if task:
                    # Обновляем данные задачи
                    task.name = name
                    task.interval_type = interval_type
                    task.interval_value = interval_value
                    task.time_of_day = time_of_day
                    
                    # Обновляем типы задач
                    if task_type_names:
                        task_types = session.query(TaskTypeDefinition).filter(TaskTypeDefinition.name.in_(task_type_names)).all()
                        task.task_types = task_types
                    
                    session.flush()  # Принудительно записываем в БД, но не коммитим транзакцию
                    
                    # Получаем обновленные данные
                    assigned_group_ids = [group.id for group in task.groups] if hasattr(task, 'groups') else []
                    assigned_task_type_ids = [task_type.id for task_type in task.task_types] if hasattr(task, 'task_types') else []
                    
                    result = {
                        'id': task.id,
                        'name': task.name,
                        'task_types': assigned_task_type_ids,
                        'interval_type': task.interval_type,
                        'interval_value': task.interval_value,
                        'time_of_day': task.time_of_day,
                        'is_active': task.is_active,
                        'assigned_groups': assigned_group_ids,
                        'last_run': task.last_run.isoformat() if task.last_run else None,
                        'created_at': task.created_at.isoformat() if task.created_at else None
                    }
                    
                    logger.info(f"Обновлена задача с ID {task_id}")
                    return result
                logger.warning(f"Задача с ID {task_id} не найдена")
                return None
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при обновлении задачи с ID {task_id}: {e}")
                raise
    
    # Методы для работы с уведомлениями
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
                    logger.info(f"Получено уведомление с ID {notification_id}")
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
                logger.info(f"Получено {len(notifications)} уведомлений для группы {group_id}")
                return notifications
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при получении уведомлений для группы {group_id}: {e}")
                raise
    
    # Методы для получения статистики
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
                recent_notifications = self.get_notifications(limit=5)
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

# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()