from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime

Base = declarative_base()

class Admin(Base):
    """Модель администратора"""
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Admin(username={self.username})>'

class Group(Base):
    """Модель группы Telegram"""
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String(50), unique=True, nullable=False, index=True)  # ID группы в Telegram
    name = Column(String(100), nullable=False)  # Название группы
    addresses = Column(Text) # Адреса, которые отслеживает группа (JSON)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связь с запланированными задачами
    scheduled_tasks = relationship("ScheduledTask", secondary="task_groups", back_populates="groups")
    
    def __repr__(self):
        return f'<Group(name={self.name}, group_id={self.group_id})>'

class Outage(Base):
    """Модель отключения"""
    __tablename__ = 'outages'
    
    id = Column(Integer, primary_key=True)
    district = Column(String(100), index=True)  # Район
    resource = Column(String(50), index=True)  # Ресурс (электричество, вода и т.д.)
    organization = Column(String(100))  # Организация
    phone = Column(String(50))  # Телефон
    addresses = Column(Text)  # Адреса (JSON)
    reason = Column(String(200))  # Причина
    start_time = Column(String(50))  # Время начала
    end_time = Column(String(50))  # Время окончания
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    notified = Column(Boolean, default=False, index=True)  # Отправлено ли уведомление
    content_hash = Column(String(64), unique=True, index=True)  # Хэш содержимого для проверки дубликатов
    
    def __repr__(self):
        return f'<Outage(district={self.district}, resource={self.resource})>'

# Таблица связей между задачами и группами
task_groups = Table('task_groups', Base.metadata,
    Column('task_id', Integer, ForeignKey('scheduled_tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('group_id', Integer, ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_task_group_task_id', 'task_id'),
    Index('idx_task_group_group_id', 'group_id')
)

# Таблица связей между задачами и типами задач
task_types = Table('task_types', Base.metadata,
    Column('task_id', Integer, ForeignKey('scheduled_tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('type_id', Integer, ForeignKey('task_type_definitions.id', ondelete='CASCADE'), primary_key=True),
    Index('idx_task_type_task_id', 'task_id'),
    Index('idx_task_type_type_id', 'type_id')
)

class TaskTypeDefinition(Base):
    """Определение типа задачи"""
    __tablename__ = 'task_type_definitions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # Имя типа (outages_check, holidays_check, weather_check)
    display_name = Column(String(100), nullable=False)  # Отображаемое имя
    description = Column(Text)  # Описание
    
    # Связь с запланированными задачами
    scheduled_tasks = relationship("ScheduledTask", secondary="task_types", back_populates="task_types")
    
    def __repr__(self):
        return f'<TaskTypeDefinition(name={self.name})>'

class ScheduledTask(Base):
    """Модель запланированной задачи"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)  # Название задачи
    interval_type = Column(String(20), nullable=False, index=True)  # Тип интервала (minute, hour, day, week, month)
    interval_value = Column(Integer, nullable=False)  # Значение интервала
    time_of_day = Column(String(10), index=True)  # Время суток для выполнения (HH:MM)
    is_active = Column(Boolean, default=True, index=True)
    last_run = Column(DateTime, index=True)  # Последний запуск
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связь с группами
    groups = relationship("Group", secondary=task_groups, back_populates="scheduled_tasks")
    
    # Связь с типами задач
    task_types = relationship("TaskTypeDefinition", secondary=task_types, back_populates="scheduled_tasks")
    
    def __repr__(self):
        return f'<ScheduledTask(name={self.name})>'

class Notification(Base):
    """Модель уведомления"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)  # Тип события (outage, holiday, weather)
    event_id = Column(Integer, index=True)  # ID события в соответствующей таблице
    group_id = Column(String(50), index=True)  # ID группы, куда отправлено уведомление
    message = Column(Text)  # Текст уведомления
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)  # Время отправки
    is_duplicate = Column(Boolean, default=False, index=True)  # Является ли дубликатом
    
    def __repr__(self):
        return f'<Notification(event_type={self.event_type}, group_id={self.group_id})>'