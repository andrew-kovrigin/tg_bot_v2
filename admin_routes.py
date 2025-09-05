import logging
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from databases.manager import db_manager
from databases.models import ScheduledTask, TaskTypeDefinition
from decorators import login_required
from security import security_manager, csrf_protect
import json
import hashlib

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создаем Blueprint для админки
admin_bp = Blueprint('admin', __name__)

# Файл-флаг для обновления задач планировщика
REFRESH_FLAG_FILE = "scheduler_refresh.flag"

def create_refresh_flag():
    """Создает файл-флаг для обновления задач планировщика"""
    try:
        with open(REFRESH_FLAG_FILE, 'w') as f:
            f.write("refresh")
        logger.info("Файл-флаг обновления задач планировщика создан")
    except Exception as e:
        logger.error(f"Ошибка при создании файла-флага: {e}")

# Маршрут для входа в систему
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа в систему"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Введите имя пользователя и пароль')
            return render_template('login.html')
        
        # Проверяем существование администратора и совпадение пароля
        admin = db_manager.get_admin_by_username(username)
        if admin:
            # Проверяем пароль с помощью security_manager
            if security_manager.verify_password(password, admin.password_hash):
                # Устанавливаем сессию
                session['username'] = username
                flash('Вы успешно вошли в систему', 'success')
                return redirect(url_for('admin.index'))
        
        flash('Неверное имя пользователя или пароль')
        return render_template('login.html')
    
    # GET запрос - отображаем форму входа
    return render_template('login.html')

# Маршрут для выхода из системы
@admin_bp.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('username', None)
    # Удаляем CSRF токен при выходе
    session.pop('csrf_token', None)
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('admin.login'))

# Маршрут для главной страницы админки
@admin_bp.route('/')
@login_required
def index():
    """Главная страница админки"""
    try:
        # Получаем статистику для отображения на главной странице
        system_stats = db_manager.get_system_stats()
        duplicate_stats = db_manager.get_duplicate_stats()
        
        stats = {
            'groups_count': system_stats.get('counts', {}).get('groups', 0),
            'outages_count': system_stats.get('counts', {}).get('outages', 0),
            'notifications_count': system_stats.get('counts', {}).get('notifications', 0),
            'duplicates_prevented': duplicate_stats.get('duplicates_prevented', 0),
            'duplicate_percentage': duplicate_stats.get('duplicate_percentage', 0)
        }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики для главной страницы: {e}")
        return render_template('index.html', stats={'groups_count': 0, 'outages_count': 0, 'notifications_count': 0, 'duplicates_prevented': 0, 'duplicate_percentage': 0})

# Маршрут для страницы дубликатов
@admin_bp.route('/duplicate_prevention')
@login_required
def duplicate_prevention():
    """Страница информации о системе предотвращения дубликатов"""
    return render_template('duplicate_prevention.html')

# Маршрут для страницы уведомлений
@admin_bp.route('/notifications')
@login_required
def notifications():
    """Страница истории уведомлений"""
    return render_template('notifications.html')

# Маршруты для работы с администраторами
@admin_bp.route('/admins')
@login_required
def admins():
    """Страница управления администраторами"""
    return render_template('admins.html')

# API для получения списка администраторов
@admin_bp.route('/api/admins', methods=['GET'])
@login_required
def api_get_admins():
    """API для получения списка администраторов"""
    try:
        admins = db_manager.get_all_admins()
        admins_data = []
        for admin in admins:
            admins_data.append({
                'id': admin.id,
                'username': admin.username,
                'created_at': admin.created_at.isoformat() if admin.created_at else None
            })
        
        return jsonify(admins_data)
    except Exception as e:
        logger.error(f"Ошибка при получении списка администраторов: {e}")
        return jsonify({'error': str(e)}), 500

# API для добавления нового администратора
@admin_bp.route('/api/admins', methods=['POST'])
@login_required
@csrf_protect
def api_add_admin():
    """API для добавления нового администратора"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not username or not password or not confirm_password:
            return jsonify({'error': 'Username, password and confirm_password are required'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Проверяем, что пользователь с таким именем не существует
        existing_admin = db_manager.get_admin_by_username(username)
        if existing_admin:
            return jsonify({'error': 'Admin with this username already exists'}), 400
        
        # Хешируем пароль с помощью security_manager
        password_hash = security_manager.hash_password(password)
        
        # Добавляем нового администратора
        admin = db_manager.add_admin(username, password_hash)
        
        result = {
            'id': admin.id,
            'username': admin.username,
            'created_at': admin.created_at.isoformat() if admin.created_at else None
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при добавлении администратора: {e}")
        return jsonify({'error': str(e)}), 500

# API для удаления администратора
@admin_bp.route('/api/admins/<int:admin_id>', methods=['DELETE'])
@login_required
@csrf_protect
def api_delete_admin(admin_id):
    """API для удаления администратора"""
    try:
        # Используем контекстный менеджер для работы с сессией
        result = db_manager.delete_admin(admin_id)
        if result:
            return jsonify({'message': 'Admin deleted successfully'})
        else:
            return jsonify({'error': 'Admin not found or cannot delete the last admin'}), 404
    except Exception as e:
        logger.error(f"Ошибка при удалении администратора: {e}")
        return jsonify({'error': str(e)}), 500

# Маршруты для работы с группами
@admin_bp.route('/groups')
@login_required
def groups():
    """Страница управления группами"""
    return render_template('groups.html')

@admin_bp.route('/api/groups', methods=['GET'])
@login_required
def api_get_groups():
    """API для получения списка групп"""
    try:
        logger.info("Получение списка групп")
        groups = db_manager.get_all_groups()
        groups_data = []
        for group in groups:
            try:
                addresses = json.loads(group.addresses) if group.addresses else []
            except Exception as e:
                logger.warning(f"Ошибка при парсинге адресов группы {group.id}: {e}")
                addresses = []
            
            groups_data.append({
                'id': group.id,
                'group_id': group.group_id,
                'name': group.name,
                'addresses': addresses,
                'is_active': group.is_active,
                'created_at': group.created_at.isoformat() if group.created_at else None
            })
        logger.info(f"Успешно получено {len(groups_data)} групп")
        return jsonify(groups_data)
    except Exception as e:
        logger.error(f"Ошибка при получении списка групп: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/groups', methods=['POST'])
@login_required
@csrf_protect
def api_add_group():
    """API для добавления новой группы"""
    try:
        data = request.get_json()
        group_id = data.get('group_id')
        name = data.get('name')
        addresses = data.get('addresses', [])
        
        if not group_id or not name:
            logger.warning("Попытка добавить группу без обязательных полей")
            return jsonify({'error': 'group_id and name are required'}), 400
        
        logger.info(f"Добавление новой группы: {name} ({group_id})")
        group = db_manager.add_group(group_id, name, addresses)
        
        # Создаем файл-флаг для обновления задач в планировщике
        create_refresh_flag()
        
        result = {
            'id': group.id,
            'group_id': group.group_id,
            'name': group.name,
            'addresses': addresses,
            'is_active': group.is_active,
            'created_at': group.created_at.isoformat() if group.created_at else None
        }
        logger.info(f"Группа успешно добавлена: {name}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при добавлении группы: {e}")
        # Проверяем, является ли ошибка дубликатом group_id
        if "UNIQUE constraint failed: groups.group_id" in str(e):
            return jsonify({'error': 'Группа с таким ID уже существует'}), 400
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/groups/<int:group_id>', methods=['PUT'])
@login_required
@csrf_protect
def api_update_group(group_id):
    """API для обновления группы"""
    try:
        data = request.get_json()
        name = data.get('name')
        addresses = data.get('addresses', [])
        
        if not name:
            logger.warning("Попытка обновить группу без обязательных полей")
            return jsonify({'error': 'name is required'}), 400
        
        logger.info(f"Обновление группы с ID: {group_id}")
        # Используем контекстный менеджер для работы с сессией
        result = db_manager.update_group(group_id, name, addresses)
        if result:
            # Создаем файл-флаг для обновления задач в планировщике
            create_refresh_flag()
            logger.info(f"Группа с ID {group_id} успешно обновлена")
            return jsonify(result)
        else:
            logger.warning(f"Группа с ID {group_id} не найдена")
            return jsonify({'error': 'Group not found'}), 404
    except Exception as e:
        logger.error(f"Ошибка при обновлении группы: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
@login_required
@csrf_protect
def api_delete_group(group_id):
    """API для удаления группы"""
    try:
        logger.info(f"Удаление группы с ID: {group_id}")
        # Используем контекстный менеджер для работы с сессией
        result = db_manager.deactivate_group(group_id)
        if result:
            # Создаем файл-флаг для обновления задач в планировщике
            create_refresh_flag()
            logger.info(f"Группа с ID {group_id} помечена как неактивная")
            return jsonify({'message': 'Group deactivated successfully'})
        else:
            logger.warning(f"Группа с ID {group_id} не найдена")
            return jsonify({'error': 'Group not found'}), 404
    except Exception as e:
        logger.error(f"Ошибка при удалении группы: {e}")
        return jsonify({'error': str(e)}), 500

# Маршруты для работы с планировщиком
@admin_bp.route('/scheduler')
@login_required
def scheduler_page():
    """Страница управления планировщиком"""
    return render_template('scheduler.html')

@admin_bp.route('/api/scheduled_tasks', methods=['GET'])
@login_required
def api_get_scheduled_tasks():
    """API для получения списка запланированных задач"""
    try:
        tasks_data = db_manager.get_active_scheduled_tasks()
        result = []
        for task_data in tasks_data:
            # Форматируем даты для JSON
            formatted_task = task_data.copy()
            formatted_task['last_run'] = task_data['last_run'].isoformat() if task_data['last_run'] else None
            formatted_task['created_at'] = task_data['created_at'].isoformat() if task_data['created_at'] else None
            result.append(formatted_task)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при получении списка задач: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/scheduled_tasks', methods=['POST'])
@login_required
@csrf_protect
def api_add_scheduled_task():
    """API для добавления новой запланированной задачи"""
    try:
        data = request.get_json()
        name = data.get('name')
        task_type_names = data.get('task_types', [])  # Теперь список типов задач
        interval_type = data.get('interval_type')
        interval_value = data.get('interval_value')
        time_of_day = data.get('time_of_day')
        group_ids = data.get('group_ids', [])
        
        if not name or not task_type_names or not interval_type or not interval_value:
            logger.warning("Попытка добавить задачу без обязательных полей")
            return jsonify({'error': 'name, task_types, interval_type and interval_value are required'}), 400
        
        logger.info(f"Добавление новой задачи: {name}")
        task_data = db_manager.add_scheduled_task(
            name=name,
            task_type_names=task_type_names,  # Список типов задач
            interval_type=interval_type,
            interval_value=interval_value,
            time_of_day=time_of_day,
            group_ids=group_ids
        )
        
        # Создаем файл-флаг для обновления задач в планировщике
        create_refresh_flag()
        
        # Форматируем даты для JSON
        result = task_data.copy()
        result['last_run'] = task_data['last_run'].isoformat() if task_data['last_run'] else None
        result['created_at'] = task_data['created_at'].isoformat() if task_data['created_at'] else None
        
        logger.info(f"Задача успешно добавлена: {name}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/scheduled_tasks/<int:task_id>', methods=['DELETE'])
@login_required
@csrf_protect
def api_delete_scheduled_task(task_id):
    """API для удаления запланированной задачи"""
    try:
        logger.info(f"Удаление задачи с ID: {task_id}")
        # Используем контекстный менеджер для работы с сессией
        result = db_manager.deactivate_scheduled_task(task_id)
        if result:
            # Создаем файл-флаг для обновления задач в планировщике
            create_refresh_flag()
            logger.info(f"Задача с ID {task_id} помечена как неактивная")
            return jsonify({'message': 'Task deactivated successfully'})
        else:
            logger.warning(f"Задача с ID {task_id} не найдена")
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {e}")
        return jsonify({'error': str(e)}), 500

# API для получения запланированной задачи по ID
@admin_bp.route('/api/scheduled_tasks/<int:task_id>', methods=['GET'])
@login_required
def api_get_scheduled_task(task_id):
    """API для получения запланированной задачи по ID"""
    try:
        logger.info(f"Получение задачи с ID: {task_id}")
        # Получаем задачу по ID
        tasks_data = db_manager.get_all_scheduled_tasks()
        task_data = next((task for task in tasks_data if task['id'] == task_id), None)
        
        if task_data:
            # Форматируем даты для JSON
            result = task_data.copy()
            result['last_run'] = task_data['last_run'].isoformat() if task_data['last_run'] else None
            result['created_at'] = task_data['created_at'].isoformat() if task_data['created_at'] else None
            logger.info(f"Задача с ID {task_id} успешно получена")
            return jsonify(result)
        else:
            logger.warning(f"Задача с ID {task_id} не найдена")
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        logger.error(f"Ошибка при получении задачи: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/scheduled_tasks/<int:task_id>', methods=['PUT'])
@login_required
@csrf_protect
def api_update_scheduled_task(task_id):
    """API для обновления запланированной задачи"""
    try:
        data = request.get_json()
        name = data.get('name')
        task_type_names = data.get('task_types', [])  # Теперь список типов задач
        interval_type = data.get('interval_type')
        interval_value = data.get('interval_value')
        time_of_day = data.get('time_of_day')
        
        if not name or not task_type_names or not interval_type or not interval_value:
            logger.warning("Попытка обновить задачу без обязательных полей")
            return jsonify({'error': 'name, task_types, interval_type and interval_value are required'}), 400
        
        logger.info(f"Обновление задачи с ID: {task_id}")
        # Используем контекстный менеджер для работы с сессией
        result = db_manager.update_scheduled_task(
            task_id=task_id,
            name=name,
            task_type_names=task_type_names,
            interval_type=interval_type,
            interval_value=interval_value,
            time_of_day=time_of_day
        )
        if result:
            # Создаем файл-флаг для обновления задач в планировщике
            create_refresh_flag()
            logger.info(f"Задача с ID {task_id} успешно обновлена")
            return jsonify(result)
        else:
            logger.warning(f"Задача с ID {task_id} не найдена")
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        logger.error(f"Ошибка при обновлении задачи: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/task_types', methods=['GET'])
@login_required
def api_get_task_types():
    """API для получения списка типов задач"""
    try:
        task_types = db_manager.get_all_task_types()
        result = []
        for task_type in task_types:
            task_type_data = {
                'id': task_type.id,
                'name': task_type.name,
                'display_name': task_type.display_name,
                'description': task_type.description
            }
            result.append(task_type_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при получении списка типов задач: {e}")
        return jsonify({'error': str(e)}), 500

# Маршруты для работы с уведомлениями
@admin_bp.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    """API для получения списка уведомлений"""
    try:
        logger.info("Получение списка уведомлений")
        # Получаем параметры фильтрации
        event_type = request.args.get('event_type')
        
        if event_type:
            notifications = db_manager.get_notifications_by_type(event_type, limit=100)
        else:
            notifications = db_manager.get_notifications(limit=100)
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'event_type': notification.event_type,
                'event_id': notification.event_id,
                'group_id': notification.group_id,
                'message': notification.message,
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'is_duplicate': notification.is_duplicate
            })
        logger.info(f"Успешно получено {len(notifications_data)} уведомлений")
        return jsonify(notifications_data)
    except Exception as e:
        logger.error(f"Ошибка при получении списка уведомлений: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/notifications/<int:notification_id>', methods=['GET'])
@login_required
def api_get_notification(notification_id):
    """API для получения деталей уведомления"""
    try:
        logger.info(f"Получение деталей уведомления с ID: {notification_id}")
        notification = db_manager.get_notification_by_id(notification_id)
        if notification:
            result = {
                'id': notification.id,
                'event_type': notification.event_type,
                'event_id': notification.event_id,
                'group_id': notification.group_id,
                'message': notification.message,
                'sent_at': notification.sent_at.isoformat() if notification.sent_at else None,
                'is_duplicate': notification.is_duplicate
            }
            logger.info(f"Уведомление с ID {notification_id} успешно получено")
            return jsonify(result)
        else:
            logger.warning(f"Уведомление с ID {notification_id} не найдено")
            return jsonify({'error': 'Notification not found'}), 404
    except Exception as e:
        logger.error(f"Ошибка при получении уведомления: {e}")
        return jsonify({'error': str(e)}), 500

# Маршрут для добавления группы через Telegram
@admin_bp.route('/api/add_group_from_telegram', methods=['POST'])
def api_add_group_from_telegram():
    """API для добавления группы через Telegram"""
    try:
        data = request.get_json()
        group_id = data.get('group_id')
        name = data.get('name')
        addresses = data.get('addresses', [])
        
        if not group_id or not name:
            logger.warning("Попытка добавить группу без обязательных полей")
            return jsonify({'error': 'group_id and name are required'}), 400
        
        logger.info(f"Добавление новой группы через Telegram: {name} ({group_id})")
        group = db_manager.add_group(group_id, name, addresses)
        
        # Создаем файл-флаг для обновления задач в планировщике
        create_refresh_flag()
        
        result = {
            'id': group.id,
            'group_id': group.group_id,
            'name': group.name,
            'addresses': addresses,
            'is_active': group.is_active,
            'created_at': group.created_at.isoformat() if group.created_at else None
        }
        logger.info(f"Группа успешно добавлена через Telegram: {name}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при добавлении группы через Telegram: {e}")
        # Проверяем, является ли ошибка дубликатом group_id
        if "UNIQUE constraint failed: groups.group_id" in str(e):
            return jsonify({'error': 'Группа с таким ID уже существует'}), 400
        return jsonify({'error': str(e)}), 500

# Маршрут для отправки сообщений
@admin_bp.route('/send_message')
@login_required
def send_message():
    """Страница отправки сообщений"""
    return render_template('send_message.html')

# API для получения информации о группе
@admin_bp.route('/api/get_chat_info', methods=['POST'])
@login_required
@csrf_protect
def api_get_chat_info():
    """API для получения информации о чате через Telegram Bot API"""
    try:
        data = request.get_json()
        chat_id = data.get('chat_id')
        
        if not chat_id:
            return jsonify({'error': 'chat_id is required'}), 400
        
        # Импортируем бота и получаем информацию о чате
        from aiogram import Bot
        from data.config import TELEGRAM_TOKEN
        import asyncio
        
        bot = Bot(token=TELEGRAM_TOKEN)
        
        # Создаем event loop для асинхронного вызова
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            chat = loop.run_until_complete(bot.get_chat(chat_id=chat_id))
            loop.close()
            
            return jsonify({
                'id': chat.id,
                'title': chat.title or chat.username or chat.first_name or f"Chat {chat.id}",
                'type': chat.type
            })
        except Exception as e:
            loop.close()
            logger.error(f"Ошибка при получении информации о чате {chat_id}: {e}")
            return jsonify({'error': f'Failed to get chat info: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Ошибка в api_get_chat_info: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/send_message', methods=['POST'])
@login_required
@csrf_protect
def api_send_message():
    """API для отправки сообщения в группы"""
    try:
        data = request.get_json()
        message = data.get('message')
        group_ids = data.get('group_ids', [])
        
        if not message:
            logger.warning("Попытка отправить пустое сообщение")
            return jsonify({'error': 'Message is required'}), 400
        
        logger.info(f"Отправка сообщения в {len(group_ids) if group_ids else 'все'} групп(ы)")
        
        # Получаем группы
        if group_ids:
            groups = db_manager.get_groups_by_ids(group_ids)
        else:
            groups = db_manager.get_all_groups()
        
        if not groups:
            logger.warning("Не найдено активных групп для отправки сообщения")
            return jsonify({'error': 'No active groups found'}), 400
        
        # Отправляем сообщение
        from aiogram import Bot
        from data.config import TELEGRAM_TOKEN
        import asyncio
        bot = Bot(token=TELEGRAM_TOKEN)
        
        sent_count = 0
        error_count = 0
        
        # Создаем event loop для асинхронных вызовов
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for group in groups:
            try:
                loop.run_until_complete(bot.send_message(chat_id=group.group_id, text=message))
                logger.info(f"Сообщение отправлено в группу {group.name}")
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в группу {group.name}: {e}")
                error_count += 1
        
        loop.close()
        
        result = {
            'message': 'Messages sent successfully',
            'sent_count': sent_count,
            'error_count': error_count
        }
        logger.info(f"Отправка сообщений завершена. Успешно: {sent_count}, Ошибок: {error_count}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return jsonify({'error': str(e)}), 500

# Маршрут для получения статистики
@admin_bp.route('/api/stats')
@login_required
def api_get_stats():
    """API для получения статистики"""
    try:
        logger.info("Получение статистики системы")
        stats = db_manager.get_system_stats()
        logger.info("Статистика успешно получена")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/duplicate_stats')
@login_required
def api_get_duplicate_stats():
    """API для получения статистики по дубликатам"""
    try:
        logger.info("Получение статистики по дубликатам")
        stats = db_manager.get_duplicate_stats()
        logger.info("Статистика по дубликатам успешно получена")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики по дубликатам: {e}")
        return jsonify({'error': str(e)}), 500

# Контекстный процессор для передачи CSRF токена в шаблоны
@admin_bp.context_processor
def inject_csrf_token():
    """Добавляет CSRF токен в контекст шаблонов"""
    return dict(csrf_token=security_manager.generate_csrf_token())

# Контекстный процессор для передачи CSRF токена в шаблоны для JavaScript
@admin_bp.context_processor
def inject_csrf_token_for_js():
    """Добавляет CSRF токен в контекст шаблонов для использования в JavaScript"""
    return dict(csrf_token_js=security_manager.generate_csrf_token())