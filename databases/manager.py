from databases.database import create_database
from databases.admin_manager import AdminManager
from databases.group_manager import GroupManager
from databases.outage_manager import OutageManager
from databases.task_manager import TaskManager
from databases.notification_manager import NotificationManager
from databases.stats_manager import StatsManager

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.engine = create_database()
        self._init_managers()
    
    def _init_managers(self):
        """Инициализация всех менеджеров"""
        self.admin_manager = AdminManager(self.engine)
        self.group_manager = GroupManager(self.engine)
        self.outage_manager = OutageManager(self.engine)
        self.task_manager = TaskManager(self.engine)
        self.notification_manager = NotificationManager(self.engine)
        self.stats_manager = StatsManager(self.engine)
    
    # Delegate methods to AdminManager
    def add_admin(self, username: str, password_hash: str):
        return self.admin_manager.add_admin(username, password_hash)
    
    def get_admin_by_username(self, username: str):
        return self.admin_manager.get_admin_by_username(username)
    
    def get_all_admins(self):
        return self.admin_manager.get_all_admins()
    
    def delete_admin(self, admin_id: int) -> bool:
        return self.admin_manager.delete_admin(admin_id)
    
    # Delegate methods to GroupManager
    def add_group(self, group_id: str, name: str, addresses: list):
        return self.group_manager.add_group(group_id, name, addresses)
    
    def get_all_groups(self):
        return self.group_manager.get_all_groups()
    
    def get_group_by_id(self, group_id: str):
        return self.group_manager.get_group_by_id(group_id)
    
    def get_groups_by_ids(self, group_ids: list):
        return self.group_manager.get_groups_by_ids(group_ids)
    
    def update_group_addresses(self, group_id: str, addresses: list) -> bool:
        return self.group_manager.update_group_addresses(group_id, addresses)
    
    def update_group(self, group_id: int, name: str, addresses: list):
        return self.group_manager.update_group(group_id, name, addresses)
    
    def deactivate_group(self, group_id: int) -> bool:
        return self.group_manager.deactivate_group(group_id)
    
    # Delegate methods to OutageManager
    def add_outages(self, outages_data: list):
        return self.outage_manager.add_outages(outages_data)
    
    def get_unnotified_outages(self):
        return self.outage_manager.get_unnotified_outages()
    
    def get_outages_by_date_range(self, start_date, end_date):
        return self.outage_manager.get_outages_by_date_range(start_date, end_date)
    
    def mark_outages_as_notified(self, outage_ids: list) -> bool:
        return self.outage_manager.mark_outages_as_notified(outage_ids)
    
    # Delegate methods to TaskManager
    def add_scheduled_task(self, name: str, task_type_names: list, interval_type: str, 
                          interval_value: int, time_of_day: str = None, group_ids: list = None):
        return self.task_manager.add_scheduled_task(name, task_type_names, interval_type, interval_value, time_of_day, group_ids)
    
    def get_all_scheduled_tasks(self):
        return self.task_manager.get_all_scheduled_tasks()
    
    def get_active_scheduled_tasks(self):
        return self.task_manager.get_active_scheduled_tasks()
    
    def get_task_type_by_id(self, type_id: int):
        return self.task_manager.get_task_type_by_id(type_id)
    
    def get_all_task_types(self):
        return self.task_manager.get_all_task_types()
    
    def initialize_task_types(self):
        return self.task_manager.initialize_task_types()
    
    def get_task_groups(self, task_id: int):
        return self.task_manager.get_task_groups(task_id)
    
    def deactivate_scheduled_task(self, task_id: int) -> bool:
        return self.task_manager.deactivate_scheduled_task(task_id)
    
    def update_scheduled_task(self, task_id: int, name: str, task_type_names: list, 
                             interval_type: str, interval_value: int, time_of_day: str = None):
        return self.task_manager.update_scheduled_task(task_id, name, task_type_names, interval_type, interval_value, time_of_day)
    
    # Delegate methods to NotificationManager
    def add_notification(self, event_type: str, event_id: int, group_id: str, message: str, is_duplicate: bool = False):
        return self.notification_manager.add_notification(event_type, event_id, group_id, message, is_duplicate)
    
    def get_notifications(self, limit: int = 100):
        return self.notification_manager.get_notifications(limit)
    
    def get_notifications_by_type(self, event_type: str, limit: int = 100):
        return self.notification_manager.get_notifications_by_type(event_type, limit)
    
    def get_notification_by_id(self, notification_id: int):
        return self.notification_manager.get_notification_by_id(notification_id)
    
    def get_notifications_by_group(self, group_id: str, limit: int = 100):
        return self.notification_manager.get_notifications_by_group(group_id, limit)
    
    # Delegate methods to StatsManager
    def get_system_stats(self):
        return self.stats_manager.get_system_stats()
    
    def get_duplicate_stats(self):
        return self.stats_manager.get_duplicate_stats()

# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()