from databases.base_manager import BaseManager
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from databases.models import Admin
import logging
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logger = logging.getLogger(__name__)

class AdminManager(BaseManager):
    """Менеджер для работы с администраторами"""
    
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
                    # Отсоединяем объект от сессии после завершения запроса
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
                # Отсоединяем все объекты от сессии после завершения запроса
                for admin in admins:
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