from flask import jsonify, render_template, request
import logging
import traceback

# Настройка логирования
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Регистрация обработчиков ошибок для Flask приложения"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Обработчик ошибки 404"""
        logger.warning(f"404 ошибка: {request.url}")
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Обработчик ошибки 500"""
        logger.error(f"500 ошибка: {error}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Обработчик всех необработанных исключений"""
        # Передаем исключение обработчику 500, если это HTTP ошибка
        if hasattr(e, 'code'):
            return internal_error(e)
        
        # Логируем неожиданное исключение
        logger.error(f"Необработанное исключение: {e}", exc_info=True)
        
        # Возвращаем JSON ошибку для API запросов
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500
        
        # Для обычных запросов возвращаем страницу ошибки
        return render_template('500.html'), 500

def log_exception(sender, exception, **extra):
    """Логирование исключений"""
    logger.error(f"Исключение в приложении: {exception}", exc_info=True)