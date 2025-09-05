import asyncio
import logging
from datetime import datetime
from utils.outages_parser import parse_outages
from databases.manager import db_manager
from aiogram import Bot
from data.config import TELEGRAM_TOKEN
import json
import re

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Scheduler:
    """Планировщик задач"""
    
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
    
    async def execute_task(self, task):
        """Выполнение задачи"""
        try:
            logger.info(f"=== НАЧАЛО ВЫПОЛНЕНИЯ ЗАДАЧИ: {task['name']} (ID: {task['id']}) ===")
            
            # Получаем типы задач для этой задачи
            task_type_objects = self._get_task_types(task)
            
            if not task_type_objects:
                logger.warning(f"Для задачи {task['name']} не найдены типы задач")
                return
            
            # Получаем группы для этой задачи
            groups = self._get_task_groups(task)
            
            # Сбор данных для всех типов задач
            outages_data = self._collect_task_outages(task_type_objects)
            
            # Подготовка сообщений
            messages = self._prepare_messages(groups, outages_data)
            
            # Отправка уведомлений
            await self._send_notifications(groups, messages, outages_data)
            
            # Обновляем время последнего запуска задачи
            self._update_task_last_run_time(task)
                
            logger.info(f"=== ЗАВЕРШЕНИЕ ВЫПОЛНЕНИЯ ЗАДАЧИ: {task['name']} ===")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при выполнении задачи {task['name']}: {e}", exc_info=True)
    
    
    def _format_outages_message(self, outages, group=None):
        """Форматирование сообщения об отключениях"""
        if not outages:
            return "Нет данных об отключениях."
        
        message = "<b>⚠️ Обнаружены отключения коммунальных услуг:</b>\n\n"
        
        for outage in outages:
            # Форматируем адреса - если передана группа, показываем только отфильтрованный адрес
            addresses_text = ""
            try:
                addresses = json.loads(outage.addresses) if outage.addresses else []
                if addresses:
                    if group and group.addresses:
                        # Получаем адреса группы для фильтрации
                        group_addresses = json.loads(group.addresses) if group.addresses else []
                        # Находим совпавший адрес
                        matched_address = self._find_matched_address(group_addresses, addresses)
                        if matched_address:
                            # Показываем только совпавший адрес
                            street = matched_address.get('street', '')
                            houses = matched_address.get('houses', [])
                            if houses:
                                addresses_text = f"{street} ({', '.join(houses)})"
                            else:
                                addresses_text = street
                        else:
                            # Если не удалось определить совпавший адрес, показываем все адреса
                            addresses_parts = []
                            for addr in addresses:
                                street = addr.get('street', '')
                                houses = addr.get('houses', [])
                                if houses:
                                    addresses_parts.append(f"{street} ({', '.join(houses)})")
                                else:
                                    addresses_parts.append(street)
                            addresses_text = "; ".join(addresses_parts)
                    else:
                        # Если группа не передана, показываем все адреса
                        addresses_parts = []
                        for addr in addresses:
                            street = addr.get('street', '')
                            houses = addr.get('houses', [])
                            if houses:
                                addresses_parts.append(f"{street} ({', '.join(houses)})")
                            else:
                                addresses_parts.append(street)
                        addresses_text = "; ".join(addresses_parts)
            except Exception as e:
                logger.warning(f"Ошибка при парсинге адресов: {e}")
                addresses_text = outage.addresses or ""
            
            # Формируем текст для одного отключения
            outage_text = f"<b>🏢 Район:</b> {outage.district}\n"
            outage_text += f"<b>💡 Ресурс:</b> {outage.resource}\n"
            if outage.organization:
                outage_text += f"<b>🏢 Организация:</b> {outage.organization}\n"
            if outage.phone:
                outage_text += f"<b>📞 Телефон:</b> {outage.phone}\n"
            if addresses_text:
                outage_text += f"<b>📍 Адреса:</b> {addresses_text}\n"
            if outage.reason:
                outage_text += f"<b>📝 Причина:</b> {outage.reason}\n"
            if outage.start_time and outage.end_time:
                outage_text += f"<b>⏰ Время:</b> {outage.start_time} - {outage.end_time}\n"
            outage_text += "\n"
            
            # Проверяем, не превысит ли добавление этого отключения лимит
            if len(message + outage_text) > 3500:  # Оставляем запас для безопасности
                # Добавляем информацию о том, что есть еще отключения
                remaining_count = len(outages) - outages.index(outage)
                if remaining_count > 0:
                    message += f"...и еще {remaining_count} отключений\n\n"
                break
            else:
                message += outage_text
        
        return message
    
    def _normalize_street_name(self, street_name):
        """Очистка названия улицы от типов улиц и лишних символов"""
        return re.sub(
            r'\s*(улица|ул\.?|проспект|пр-т|переулок|пер\.?|площадь|пл\.?|проезд|бульвар|б-р|набережная|наб\.?)\s*$',
            '',
            street_name
        ).strip()
    
    def _address_match_utility(self, group_addr, outage_addr):
        """Утилита для сравнения адресов (вспомогательный метод)"""
        try:
            outage_street = outage_addr.get('street', '').lower().strip()
            outage_houses = [h.lower().strip() for h in outage_addr.get('houses', [])]
            
            group_addr_clean = group_addr.lower().strip()
            
            # Проверяем точное совпадение улицы
            if group_addr_clean == outage_street:
                return True, outage_addr
            
            # Проверяем совпадение с очищенными названиями улиц
            cleaned_outage_street = self._normalize_street_name(outage_street)
            cleaned_group_addr = self._normalize_street_name(group_addr_clean)
            
            # Проверяем совпадение очищенных названий улиц
            if cleaned_outage_street in cleaned_group_addr or cleaned_group_addr in cleaned_outage_street:
                # Если для улицы указаны дома, проверяем совпадение домов
                if outage_houses:
                    # Извлекаем номер дома из адреса группы (если есть)
                    house_match = re.search(r'(\d+[а-я]?)$', group_addr_clean)
                    if house_match:
                        group_house = house_match.group(1)
                        if group_house in outage_houses:
                            return True, outage_addr
                    # Если дом не указан в адресе группы, отправляем уведомление по улице
                    elif not re.search(r'\d', group_addr_clean):
                        return True, outage_addr
                else:
                    # Если дома не указаны в отключении, отправляем уведомление по улице
                    return True, outage_addr
        
            return False, None
        except Exception as e:
            logger.error(f"Ошибка при сравнении адресов: {e}")
            return False, None
    
    def _find_matched_address(self, group_addresses, outage_addresses):
        """Находит совпавший адрес между группой и отключением"""
        try:
            # Проходим по всем адресам отключения
            for outage_addr in outage_addresses:
                # Проходим по всем адресам группы
                for group_addr in group_addresses:
                    is_match, matched_address = self._address_match_utility(group_addr, outage_addr)
                    if is_match:
                        return matched_address
            
            # Если не нашли совпадение, возвращаем первый адрес
            return outage_addresses[0] if outage_addresses else None
        except Exception as e:
            logger.error(f"Ошибка при поиске совпавшего адреса: {e}")
            return outage_addresses[0] if outage_addresses else None

    
    
    def _filter_outages_by_group_addresses(self, outages, group):
        """Фильтрация отключений по адресам группы"""
        try:
            # Получаем адреса группы
            group_addresses = json.loads(group.addresses) if group.addresses else []
            
            # Если у группы нет адресов, отправляем все отключения
            if not group_addresses:
                logger.info(f"Группа {group.name} не имеет указанных адресов, отправляем все отключения")
                return outages
            
            logger.info(f"Фильтрация отключений для группы {group.name} по адресам: {group_addresses}")
            
            filtered_outages = []
            for outage in outages:
                # Парсим адреса отключения
                outage_addresses = []
                try:
                    outage_addresses = json.loads(outage.addresses) if outage.addresses else []
                except Exception as e:
                    logger.warning(f"Ошибка при парсинге адресов отключения {outage.id}: {e}")
                    continue
                
                # Проверяем, есть ли совпадение по адресам
                if self._addresses_match(group_addresses, outage_addresses):
                    filtered_outages.append(outage)
            
            logger.info(f"Отобрано {len(filtered_outages)} отключений для группы {group.name}")
            return filtered_outages
        except Exception as e:
            logger.error(f"Ошибка при фильтрации отключений для группы {group.name}: {e}")
            return outages  # Возвращаем все отключения в случае ошибки
    
    def _addresses_match(self, group_addresses, outage_addresses):
        """Проверка совпадения адресов группы и отключения"""
        try:
            # Для каждого адреса отключения проверяем совпадение с любым адресом группы
            for outage_addr in outage_addresses:
                # Для каждого адреса группы проверяем совпадение
                for group_addr in group_addresses:
                    is_match, _ = self._address_match_utility(group_addr, outage_addr)
                    if is_match:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке совпадения адресов: {e}")
            return False
    def _collect_outages_data(self):
        """Сбор данных об отключениях"""
        try:
            outages_data = parse_outages()
            logger.info(f"Получено {len(outages_data)} записей об отключениях")
            # Сохраняем данные в базу
            outages = db_manager.add_outages(outages_data)
            logger.info(f"Сохранено {len(outages)} записей в базу данных")
            return outages_data
        except Exception as e:
            logger.error(f"Ошибка при проверке отключений: {e}")
            return None
    
    
    
    def _mark_outages_as_notified(self, outages_data):
        """Пометить отключения как нотифицированные"""
        if outages_data:
            unnotified_outages = db_manager.get_unnotified_outages()
            if unnotified_outages:
                outage_ids = [outage.id for outage in unnotified_outages]
                db_manager.mark_outages_as_notified(outage_ids)
                logger.info(f"Помечено {len(outage_ids)} отключений как нотифицированные")
    
    def _add_notification_to_history(self, event_type, event_id, group_id, message):
        """Добавить уведомление в историю"""
        db_manager.add_notification(
            event_type=event_type,
            event_id=event_id,
            group_id=group_id,
            message=message
        )
    
    def _get_task_groups(self, task):
        """Получить группы для задачи"""
        task_groups = db_manager.get_task_groups(task['id'])
        
        # Если у задачи нет групп, отправляем во все активные группы
        if not task_groups:
            logger.info(f"Задача {task['name']} не имеет указанных групп, отправляем во все активные группы")
            groups = db_manager.get_all_groups()
        else:
            groups = task_groups
            logger.info(f"Задача {task['name']} настроена для {len(groups)} групп")
        
        return groups
    
    def _get_task_types(self, task):
        """Получить типы задач для этой задачи"""
        task_type_objects = []
        for type_id in task['task_types']:
            task_type_obj = db_manager.get_task_type_by_id(type_id)
            if task_type_obj:
                task_type_objects.append(task_type_obj)
        
        return task_type_objects
    
    def _update_task_last_run_time(self, task):
        """Обновить время последнего запуска задачи"""
        # Используем контекстный менеджер сессии из менеджера задач
        with db_manager.task_manager.session_manager as session:
            try:
                from databases.models import ScheduledTask
                task_obj = session.query(ScheduledTask).filter(ScheduledTask.id == task['id']).first()
                if task_obj:
                    task_obj.last_run = datetime.utcnow()
                    session.commit()
                    logger.info(f"Время последнего запуска задачи {task['name']} обновлено")
            except Exception as e:
                logger.error(f"Ошибка при обновлении времени последнего запуска задачи {task['name']}: {e}")
                # Исключение будет перехвачено и записано в вызывающем коде
                raise

    def _collect_task_outages(self, task_type_objects):
        """Сбор данных об отключениях для задачи"""
        outages_data = None
        for task_type_obj in task_type_objects:
            task_type_name = task_type_obj.name
            logger.info(f"Выполнение типа задачи: {task_type_name}")
            
            if task_type_name == 'outages_check':
                outages_data = self._collect_outages_data()
        
        return outages_data

    def _prepare_messages(self, groups, outages_data):
        """Подготовка сообщений для уведомлений"""
        messages = []
        if outages_data:
            unnotified_outages = db_manager.get_unnotified_outages()
            if unnotified_outages:
                logger.info(f"Найдено {len(unnotified_outages)} новых отключений для уведомления")
                # Фильтруем отключения по группам и формируем сообщения
                for group in groups:
                    group_outages = self._filter_outages_by_group_addresses(unnotified_outages, group)
                    if group_outages:
                        message = self._format_outages_message(group_outages, group)
                        messages.append({
                            'type': 'outage',
                            'content': message,
                            'group_id': group.group_id,
                            'outages': group_outages
                        })
            else:
                logger.info("Нет новых отключений для уведомления")
        return messages

    async def _send_notifications(self, groups, messages, outages_data):
        """Отправка уведомлений"""
        if messages:
            # Отправляем обычные уведомления
            logger.info(f"Отправка уведомлений")
            sent_count = 0
            error_count = 0
            
            # Группируем сообщения по группам
            grouped_messages = {}
            for msg in messages:
                group_id = msg['group_id']
                if group_id not in grouped_messages:
                    grouped_messages[group_id] = []
                grouped_messages[group_id].append(msg)
            
            # Отправляем сообщение для каждой группы
            for group_id, group_messages in grouped_messages.items():
                try:
                    # Объединяем все сообщения для группы в одно
                    combined_message = ""
                    for msg in group_messages:
                        combined_message += msg['content'] + "\n\n"
                    
                    # Проверяем длину сообщения
                    if len(combined_message) > 4000:
                        combined_message = combined_message[:3900] + "\n\n... (сообщение сокращено)"
                    
                    await self.bot.send_message(chat_id=group_id, text=combined_message, parse_mode="HTML")
                    logger.info(f"Отправлено уведомление в группу {group_id}")
                    
                    # Записываем в историю уведомлений (одна запись на группу)
                    self._add_notification_to_history(
                        event_type="outage",
                        event_id=1,
                        group_id=group_id,
                        message=combined_message
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления в группу {group_id}: {e}")
                    error_count += 1
            
            logger.info(f"Уведомления отправлены. Успешно: {sent_count}, Ошибок: {error_count}")
            
            # Помечаем отключения как нотифицированные (если были отключения)
            self._mark_outages_as_notified(outages_data)
        else:
            logger.info("Нет данных для отправки уведомлений")

# Глобальный экземпляр планировщика
scheduler = Scheduler()