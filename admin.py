import sys
import os
# Add the databases directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'databases'))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from databases.models import Group, Admin, UserRequest, SchedulerSettings, get_db
import databases.config as config
from sqlalchemy import func
import logging
import traceback
from datetime import datetime
import hashlib
import signal

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # Генерируем случайный секретный ключ

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_password_hash(password, hash_value):
    """Проверяет, соответствует ли пароль хэшу"""
    return hashlib.sha512(password.encode('utf-8')).hexdigest() == hash_value

def is_authenticated():
    """Проверяет, аутентифицирован ли пользователь"""
    return session.get('authenticated', False)

def require_auth(f):
    """Декоратор для защиты маршрутов"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password and config.ADMIN_PASSWORD_HASH and check_password_hash(password, config.ADMIN_PASSWORD_HASH):
            session['authenticated'] = True
            flash('Вы успешно вошли в систему', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def index():
    db = next(get_db())
    try:
        # Получаем количество групп и админов
        group_count = db.query(func.count(Group.id)).scalar()
        admin_count = db.query(func.count(Admin.id)).scalar()
        request_count = db.query(func.count(UserRequest.id)).scalar()
        
        # Получаем последние запросы пользователей
        recent_requests = db.query(UserRequest).order_by(UserRequest.created_at.desc()).limit(10).all()
        
        return render_template('index.html', 
                             group_count=group_count, 
                             admin_count=admin_count, 
                             request_count=request_count,
                             recent_requests=recent_requests)
    except Exception as e:
        logger.error(f"Ошибка при загрузке главной страницы: {str(e)}")
        return "Ошибка загрузки данных", 500
    finally:
        db.close()

@app.route('/groups')
@require_auth
def groups():
    db = next(get_db())
    try:
        groups = db.query(Group).order_by(Group.created_at.desc()).all()
        return render_template('groups.html', groups=groups)
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка групп: {str(e)}")
        return "Ошибка загрузки данных", 500
    finally:
        db.close()

@app.route('/admins')
@require_auth
def admins():
    db = next(get_db())
    try:
        admins = db.query(Admin).order_by(Admin.created_at.desc()).all()
        return render_template('admins.html', admins=admins)
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка админов: {str(e)}")
        return "Ошибка загрузки данных", 500
    finally:
        db.close()

@app.route('/requests')
@require_auth
def requests():
    db = next(get_db())
    try:
        requests = db.query(UserRequest).order_by(UserRequest.created_at.desc()).all()
        return render_template('requests.html', requests=requests)
    except Exception as e:
        logger.error(f"Ошибка при загрузке списка запросов: {str(e)}")
        return "Ошибка загрузки данных", 500
    finally:
        db.close()

@app.route('/scheduler')
@require_auth
def scheduler_settings():
    db = next(get_db())
    try:
        # Получаем все настройки планировщика
        settings = db.query(SchedulerSettings).order_by(SchedulerSettings.job_name).all()
        return render_template('scheduler.html', scheduler_settings=settings)
    except Exception as e:
        logger.error(f"Ошибка при загрузке настроек планировщика: {str(e)}")
        flash('Ошибка загрузки настроек планировщика', 'error')
        return redirect(url_for('index'))
    finally:
        db.close()

@app.route('/add_admin', methods=['POST'])
@require_auth
def add_admin():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    
    if not user_id:
        flash('Укажите ID пользователя', 'error')
        return redirect(url_for('admins'))
    
    db = next(get_db())
    try:
        # Проверяем, существует ли уже админ с таким ID
        existing_admin = db.query(Admin).filter(Admin.user_id == int(user_id)).first()
        if existing_admin:
            flash('Админ с таким ID уже существует', 'error')
            return redirect(url_for('admins'))
        
        # Добавляем нового админа
        new_admin = Admin(user_id=int(user_id), username=username)
        db.add(new_admin)
        db.commit()
        flash('Админ успешно добавлен', 'success')
    except Exception as e:
        logger.error(f"Ошибка при добавлении админа: {str(e)}")
        flash('Ошибка при добавлении админа', 'error')
    finally:
        db.close()
    
    return redirect(url_for('admins'))

@app.route('/remove_admin/<int:admin_id>', methods=['POST'])
@require_auth
def remove_admin(admin_id):
    db = next(get_db())
    try:
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if admin:
            db.delete(admin)
            db.commit()
            flash('Админ успешно удален', 'success')
        else:
            flash('Админ не найден', 'error')
    except Exception as e:
        logger.error(f"Ошибка при удалении админа: {str(e)}")
        flash('Ошибка при удалении админа', 'error')
    finally:
        db.close()
    
    return redirect(url_for('admins'))

@app.route('/edit_admin/<int:admin_id>', methods=['POST'])
@require_auth
def edit_admin(admin_id):
    username = request.form.get('username')
    
    db = next(get_db())
    try:
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if admin:
            admin.username = username
            db.commit()
            flash('Информация об админе успешно изменена', 'success')
        else:
            flash('Админ не найден', 'error')
    except Exception as e:
        logger.error(f"Ошибка при изменении информации об админе: {str(e)}")
        flash('Ошибка при изменении информации об админе', 'error')
    finally:
        db.close()
    
    return redirect(url_for('admins'))

@app.route('/send_message', methods=['POST'])
@require_auth
def send_message():
    group_ids = request.form.getlist('group_ids')
    message_text = request.form.get('message_text')
    images = request.files.getlist('images')
    
    if not group_ids or not message_text:
        flash('Выберите группы и введите текст сообщения', 'error')
        return redirect(url_for('groups'))
    
    # Отправка сообщений через Telegram API
    try:
        # Импортируем здесь, чтобы избежать циклических зависимостей
        from utils.send_message import send_messages_sync, send_messages_with_images_sync
        
        if images and any(images):
            # Если есть изображения, отправляем сообщения с изображениями
            sent_count = send_messages_with_images_sync(group_ids, message_text, images)
        else:
            # Если нет изображений, отправляем обычные сообщения
            sent_count = send_messages_sync(group_ids, message_text)
        
        flash(f'Сообщения отправлены в {sent_count} групп из {len(group_ids)}', 'success')
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщений из админки: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        flash('Ошибка при отправке сообщений', 'error')
    
    return redirect(url_for('groups'))

@app.route('/add_group', methods=['POST'])
@require_auth
def add_group():
    group_id = request.form.get('group_id')
    group_name = request.form.get('group_name')
    address = request.form.get('address')
    
    if not group_id:
        flash('Укажите ID группы', 'error')
        return redirect(url_for('groups'))
    
    db = next(get_db())
    try:
        # Проверяем, существует ли уже группа с таким ID
        existing_group = db.query(Group).filter(Group.group_id == group_id).first()
        if existing_group:
            flash('Группа с таким ID уже существует', 'error')
            return redirect(url_for('groups'))
        
        # Добавляем новую группу
        new_group = Group(
            group_id=group_id,
            group_name=group_name,
            address=address
        )
        db.add(new_group)
        db.commit()
        flash('Группа успешно добавлена', 'success')
    except Exception as e:
        logger.error(f"Ошибка при добавлении группы: {str(e)}")
        flash('Ошибка при добавлении группы', 'error')
    finally:
        db.close()
    
    return redirect(url_for('groups'))

@app.route('/remove_group/<int:group_id>', methods=['POST'])
@require_auth
def remove_group(group_id):
    db = next(get_db())
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            db.delete(group)
            db.commit()
            flash('Группа успешно удалена', 'success')
        else:
            flash('Группа не найдена', 'error')
    except Exception as e:
        logger.error(f"Ошибка при удалении группы: {str(e)}")
        flash('Ошибка при удалении группы', 'error')
    finally:
        db.close()
    
    return redirect(url_for('groups'))

@app.route('/toggle_group/<int:group_id>', methods=['POST'])
@require_auth
def toggle_group(group_id):
    db = next(get_db())
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            group.is_active = not group.is_active
            db.commit()
            flash('Статус группы изменен', 'success')
        else:
            flash('Группа не найдена', 'error')
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса группы: {str(e)}")
        flash('Ошибка при изменении статуса группы', 'error')
    finally:
        db.close()
    
    return redirect(url_for('groups'))

@app.route('/edit_group_address/<int:group_id>', methods=['POST'])
@require_auth
def edit_group_address(group_id):
    new_address = request.form.get('address')
    
    db = next(get_db())
    try:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            group.address = new_address
            db.commit()
            flash('Адрес группы успешно изменен', 'success')
        else:
            flash('Группа не найдена', 'error')
    except Exception as e:
        logger.error(f"Ошибка при изменении адреса группы: {str(e)}")
        flash('Ошибка при изменении адреса группы', 'error')
    finally:
        db.close()
    
    return redirect(url_for('groups'))

@app.route('/mark_request_completed/<int:request_id>', methods=['POST'])
@require_auth
def mark_request_completed(request_id):
    completion_comment = request.form.get('completion_comment')
    
    db = next(get_db())
    try:
        request_obj = db.query(UserRequest).filter(UserRequest.id == request_id).first()
        if request_obj:
            # Сохраняем комментарий
            request_obj.completion_comment = completion_comment
            
            # Отправляем уведомление пользователю, если это новый статус "выполнено"
            if not request_obj.is_completed:
                try:
                    # Импортируем здесь, чтобы избежать циклических зависимостей
                    from utils.send_message import send_message_sync
                    
                    # Формируем сообщение для пользователя
                    message_text = f"Ваш запрос от {request_obj.created_at.strftime('%d.%m.%Y %H:%M')} был выполнен.\\n\\n"
                    message_text += f"Запрос: {request_obj.message_text}\\n\\n"
                    if completion_comment:
                        message_text += f"Комментарий администратора: {completion_comment}"
                    
                    # Отправляем сообщение пользователю
                    send_message_sync(str(request_obj.user_id), message_text)
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления пользователю: {str(e)}")
                    logger.error(f"Трассировка стека: {traceback.format_exc()}")
            
            # Обновляем статус запроса
            request_obj.is_completed = not request_obj.is_completed
            if request_obj.is_completed:
                request_obj.completed_at = datetime.utcnow()
            
            db.commit()
            flash('Статус запроса изменен', 'success')
        else:
            flash('Запрос не найден', 'error')
    except Exception as e:
        logger.error(f"Ошибка при изменении статуса запроса: {str(e)}")
        flash('Ошибка при изменении статуса запроса', 'error')
    finally:
        db.close()
    
    return redirect(url_for('requests'))

@app.route('/update_scheduler_settings', methods=['POST'])
@require_auth
def update_scheduler_settings():
    db = next(get_db())
    try:
        # Получаем все настройки планировщика
        settings = db.query(SchedulerSettings).all()
        
        # Обновляем каждую настройку
        for setting in settings:
            # Получаем значения из формы
            is_enabled = request.form.get(f'enabled_{setting.id}') == 'on'
            interval_type = request.form.get(f'interval_type_{setting.id}')
            interval_value = request.form.get(f'interval_value_{setting.id}')
            hour = request.form.get(f'hour_{setting.id}')
            minute = request.form.get(f'minute_{setting.id}')
            day_of_month = request.form.get(f'day_of_month_{setting.id}')
            target_groups = request.form.get(f'target_groups_{setting.id}')
            
            # Получаем выбранные дни недели
            selected_days = request.form.getlist(f'days_{setting.id}')
            day_of_week = ','.join(selected_days) if selected_days else None
            
            # Обновляем значения
            setting.is_enabled = is_enabled
            setting.interval_type = interval_type
            setting.interval_value = int(interval_value) if interval_value and interval_value.isdigit() else 1
            setting.hour = int(hour) if hour and hour.isdigit() else None
            setting.minute = int(minute) if minute and minute.isdigit() else None
            setting.day_of_week = day_of_week
            setting.day_of_month = int(day_of_month) if day_of_month and day_of_month.isdigit() else None
            setting.target_groups = target_groups if target_groups else None
            
            logger.info(f"Обновлены настройки задачи {setting.job_name}: включена={is_enabled}, тип={interval_type}, значение={interval_value}")
        
        # Сохраняем изменения
        db.commit()
        flash('Настройки планировщика успешно обновлены. Изменения вступят в силу в течение 5 секунд.', 'success')
        logger.info("Настройки планировщика успешно обновлены")
    except Exception as e:
        logger.error(f"Ошибка при обновлении настроек планировщика: {str(e)}")
        logger.error(f"Трассировка стека: {traceback.format_exc()}")
        flash('Ошибка при обновлении настроек планировщика', 'error')
        db.rollback()
    finally:
        db.close()
    
    # Создаем файл-флаг для уведомления бота об обновлении
    try:
        with open(config.SCHEDULER_FLAG_FILE, "w") as f:
            f.write("update")
        logger.info("Создан файл-флаг для обновления планировщика")
    except Exception as e:
        logger.error(f"Ошибка при создании файла-флага: {str(e)}")
    
    return redirect(url_for('scheduler_settings'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)