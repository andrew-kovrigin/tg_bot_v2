from functools import wraps
from flask import redirect, url_for, session, jsonify

def login_required(f):
    """Декоратор для проверки авторизации пользователя"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            # Для API запросов возвращаем JSON ошибку
            if request_is_json():
                return jsonify({'error': 'Unauthorized'}), 401
            # Для обычных запросов перенаправляем на страницу входа
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def request_is_json():
    """Проверяет, является ли запрос API запросом (ожидает JSON ответ)"""
    from flask import request
    return (
        request.headers.get('Content-Type') == 'application/json' or
        request.headers.get('Accept') == 'application/json' or
        request.path.startswith('/api/')
    )