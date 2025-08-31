from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
import datetime
import config

Base = declarative_base()

class Group(Base):
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String(50), unique=True, nullable=False)
    group_name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Group(group_id='{self.group_id}', group_name='{self.group_name}')>"

class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Admin(user_id={self.user_id}, username='{self.username}')>"

class UserRequest(Base):
    __tablename__ = 'user_requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String(100), nullable=True)
    group_id = Column(String(50), nullable=True)
    message_text = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False)
    completion_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<UserRequest(user_id={self.user_id}, message_text='{self.message_text[:50]}...')>"

class SchedulerSettings(Base):
    __tablename__ = 'scheduler_settings'
    
    id = Column(Integer, primary_key=True)
    job_name = Column(String(100), unique=True, nullable=False)
    job_type = Column(String(50), nullable=False)  # Тип задачи: daily_message, weather, holidays, disconnections
    is_enabled = Column(Boolean, default=True)
    hour = Column(Integer, nullable=True)
    minute = Column(Integer, nullable=True)
    day_of_week = Column(String(20), nullable=True)  # Для еженедельных задач (0-6 или MON-SUN)
    day_of_month = Column(Integer, nullable=True)    # Для ежемесячных задач (1-31)
    interval_type = Column(String(20), nullable=True) # Тип интервала: minutely, hourly, daily, weekly, monthly
    interval_value = Column(Integer, nullable=True)   # Значение интервала (например, каждые 30 минут)
    target_groups = Column(Text, nullable=True)      # Список ID групп через запятую
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<SchedulerSettings(job_name='{self.job_name}', job_type='{self.job_type}', is_enabled={self.is_enabled})>"

class Disconnection(Base):
    __tablename__ = 'disconnections'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String(50))
    address = Column(Text)
    description = Column(Text)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Создание базы данных
engine = create_engine(config.DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()