from databases.base_manager import BaseManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from databases.models import ScheduledTask, TaskTypeDefinition, Group
import logging
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logger = logging.getLogger(__name__)

class TaskManager(BaseManager):
    """Менеджер для работы с запланированными задачами"""
    
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
                # Загружаем задачи вместе со связанными данными
                tasks = session.query(ScheduledTask).all()
                # Принудительно загружаем связи, чтобы они были доступны после закрытия сессии
                for task in tasks:
                    # Принудительно загружаем группы
                    if hasattr(task, 'groups'):
                        _ = [group.id for group in task.groups]
                    # Принудительно загружаем типы задач
                    if hasattr(task, 'task_types'):
                        _ = [task_type.id for task_type in task.task_types]
                
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
                # Загружаем задачи вместе со связанными данными
                tasks = session.query(ScheduledTask).filter(ScheduledTask.is_active == True).all()
                # Принудительно загружаем связи, чтобы они были доступны после закрытия сессии
                for task in tasks:
                    # Принудительно загружаем группы
                    if hasattr(task, 'groups'):
                        _ = [group.id for group in task.groups]
                    # Принудительно загружаем типы задач
                    if hasattr(task, 'task_types'):
                        _ = [task_type.id for task_type in task.task_types]
                
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
    
    def get_task_type_by_id(self, type_id: int) -> Optional[TaskTypeDefinition]:
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
                    # Отсоединяем объект от сессии после завершения запроса
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
                for task_type in task_types:
                    # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                    _ = task_type.id
                    _ = task_type.name
                    _ = task_type.display_name
                    _ = task_type.description
                # Отсоединяем все объекты от сессии после завершения запроса
                for task_type in task_types:
                    session.expunge(task_type)
                
                return task_types
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
                    for group in task.groups:
                        # Принудительно загружаем атрибуты, чтобы они были доступны после закрытия сессии
                        _ = group.id
                        _ = group.group_id
                        _ = group.name
                        _ = group.addresses
                        _ = group.is_active
                        _ = group.created_at
                    return list(task.groups)
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