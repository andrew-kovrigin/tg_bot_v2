#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных начальными данными
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databases.manager import db_manager

def initialize_database():
    """Инициализация базы данных начальными данными"""
    print("Начало инициализации базы данных...")
    
    try:
        # 1. Инициализация типов задач
        print("1. Инициализация типов задач...")
        db_manager.initialize_task_types()
        
        # 2. Создание начального администратора (если еще не создан)
        print("2. Проверка наличия администратора...")
        admin = db_manager.get_admin_by_username('admin')
        if not admin:
            print("Создание начального администратора...")
            from security import security_manager
            password_hash = security_manager.hash_password('admin')
            admin = db_manager.add_admin('admin', password_hash)
            print(f"Создан администратор: {admin.username}")
        else:
            print("Администратор 'admin' уже существует")
        
        # 3. Создание задачи по умолчанию для проверки отключений
        print("3. Создание задачи по умолчанию...")
        tasks = db_manager.get_active_scheduled_tasks()
        if not tasks:
            print("Создание задачи проверки отключений...")
            task_data = db_manager.add_scheduled_task(
                name="Проверка отключений (ежечасно)",
                task_type_names=['outages_check'],
                interval_type="hour",
                interval_value=1
            )
            print(f"Создана задача: {task_data['name']}")
        else:
            print("Задачи уже существуют")
        
        print("Инициализация базы данных завершена успешно!")
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        raise

if __name__ == '__main__':
    initialize_database()