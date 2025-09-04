import os
import hashlib
import secrets
from functools import wraps
from flask import abort, request, session
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

class SecurityManager:
    """Менеджер безопасности приложения"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Инициализация приложения"""
        # Генерируем секретный ключ, если он не установлен
        if not app.config.get('SECRET_KEY') or app.config['SECRET_KEY'] == 'your-secret-key-change-in-production':
            app.config['SECRET_KEY'] = self.generate_secret_key()
            logger.warning("Используется автоматически сгенерированный SECRET_KEY. Установите свой ключ в production.")
        
        # Добавляем заголовки безопасности
        @app.after_request
        def after_request(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response
    
    def generate_secret_key(self, length=32):
        """Генерация секретного ключа"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля с солью"""
        # Генерируем соль
        salt = secrets.token_hex(16)
        # Хешируем пароль с солью
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        # Возвращаем соль и хеш в виде строки
        return f"{salt}${pwdhash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Проверка пароля"""
        try:
            # Разделяем соль и хеш
            salt, stored_hash = hashed.split('$')
            # Хешируем введенный пароль с сохраненной солью
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
            # Сравниваем хеши
            return pwdhash.hex() == stored_hash
        except Exception as e:
            logger.error(f"Ошибка при проверке пароля: {e}")
            return False
    
    def generate_csrf_token(self):
        """Генерация CSRF токена"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']
    
    def validate_csrf_token(self, token):
        """Проверка CSRF токена"""
        logger.debug(f"Validating CSRF token. Token from request: {token}")
        logger.debug(f"CSRF token in session: {session.get('csrf_token', 'NOT FOUND')}")
        
        if 'csrf_token' not in session:
            logger.warning("CSRF token not found in session")
            return False
            
        # Ensure both values are strings before comparison
        session_token = session['csrf_token']
        logger.debug(f"Session token type: {type(session_token)}, Request token type: {type(token)}")
        
        if isinstance(session_token, bytes):
            session_token = session_token.decode('utf-8')
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            
        logger.debug(f"Comparing tokens. Session: {session_token}, Request: {token}")
        result = secrets.compare_digest(session_token, token)
        logger.debug(f"CSRF token validation result: {result}")
        return result

def csrf_protect(f):
    """Декоратор для защиты от CSRF атак"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Для GET запросов не проверяем CSRF
        if request.method in ['GET', 'HEAD', 'OPTIONS', 'TRACE']:
            return f(*args, **kwargs)
        
        # Получаем токен из формы или заголовка
        logger.debug(f"CSRF token from request form: {request.form.get('csrf_token')}")
        logger.debug(f"CSRF token from request headers: {request.headers.get('X-CSRF-Token')}")
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        logger.debug(f"Final token to validate: {token}")
        
        # Проверяем токен
        security_manager = SecurityManager()
        logger.debug(f"Token exists: {bool(token)}")
        if token:
            validation_result = security_manager.validate_csrf_token(token)
            logger.debug(f"CSRF token validation result: {validation_result}")
            if not validation_result:
                logger.warning(f"CSRF атака обнаружена от IP {request.remote_addr} - validation failed")
                abort(403)
        else:
            logger.warning(f"CSRF атака обнаружена от IP {request.remote_addr} - no token provided")
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

# Глобальный экземпляр менеджера безопасности
security_manager = SecurityManager()