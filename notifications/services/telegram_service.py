"""
Сервис для отправки уведомлений через Telegram Bot API
"""

import httpx
import time
from typing import Optional, Dict, Any
from config import settings
from utils.logging_config import setup_logging
import logging

# Настраиваем логгер для уведомлений
logger = logging.getLogger("notifications")


class TelegramService:
    """Сервис для работы с Telegram Bot API"""
    
    def __init__(self, bot_token: Optional[str] = None, api_url: Optional[str] = None):
        """
        Инициализация сервиса
        
        Args:
            bot_token: Токен Telegram бота (если не указан, берется из settings)
            api_url: URL Telegram Bot API (если не указан, берется из settings)
        """
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.api_url = api_url or settings.TELEGRAM_API_URL
        self.base_url = f"{self.api_url}{self.bot_token}"
        self.max_retries = settings.TELEGRAM_MAX_RETRIES
        self.retry_delay = settings.TELEGRAM_RETRY_DELAY
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN не установлен. Уведомления не будут отправляться.")
    
    def _make_request(
        self, 
        method: str, 
        params: Dict[str, Any],
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет запрос к Telegram Bot API
        
        Args:
            method: Метод API (например, 'sendMessage')
            params: Параметры запроса
            timeout: Таймаут запроса в секундах
            
        Returns:
            Ответ от API или None в случае ошибки
        """
        if not self.bot_token:
            logger.warning("Попытка отправить сообщение без токена бота")
            return None
        
        url = f"{self.base_url}/{method}"
        
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=params)
                response.raise_for_status()
                result = response.json()
                
                if result.get("ok"):
                    return result.get("result")
                else:
                    error_code = result.get("error_code", "unknown")
                    error_description = result.get("description", "Unknown error")
                    logger.error(f"Telegram API error (code {error_code}): {error_description}")
                    logger.debug(f"Полный ответ API: {result}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout при запросе к Telegram API: {method}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error при запросе к Telegram API: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к Telegram API: {e}")
            return None
    
    def _retry_request(
        self, 
        method: str, 
        params: Dict[str, Any],
        max_retries: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет запрос с повторными попытками при ошибках
        
        Args:
            method: Метод API
            params: Параметры запроса
            max_retries: Максимальное количество попыток (если не указано, берется из settings)
            
        Returns:
            Ответ от API или None в случае ошибки
        """
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries):
            result = self._make_request(method, params)
            
            if result is not None:
                return result
            
            # Если это не последняя попытка, ждем перед повтором
            if attempt < max_retries - 1:
                delay = self.retry_delay * (2 ** attempt)  # Экспоненциальная задержка
                logger.info(f"Повторная попытка {attempt + 2}/{max_retries} через {delay} секунд...")
                time.sleep(delay)
        
        logger.error(f"Не удалось выполнить запрос после {max_retries} попыток")
        return None
    
    def send_message(
        self, 
        telegram_id: int, 
        message: str, 
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Отправляет сообщение пользователю
        
        Args:
            telegram_id: Telegram ID пользователя
            message: Текст сообщения
            parse_mode: Режим парсинга (HTML или Markdown)
            disable_web_page_preview: Отключить предпросмотр ссылок
            
        Returns:
            True если сообщение отправлено успешно, False в противном случае
        """
        if not settings.TELEGRAM_ENABLED:
            logger.debug("Telegram уведомления отключены в настройках")
            return False
        
        if not self.bot_token:
            logger.warning("Попытка отправить сообщение без токена бота")
            return False
        
        params = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        result = self._retry_request("sendMessage", params)
        
        if result:
            message_id = result.get("message_id", "unknown")
            logger.info(f"Сообщение успешно отправлено пользователю {telegram_id} (message_id: {message_id})")
            return True
        else:
            logger.error(f"Не удалось отправить сообщение пользователю {telegram_id}")
            logger.error(f"Параметры запроса: chat_id={telegram_id}, message_length={len(message)}")
            return False
    
    def format_order_created_message(self, order) -> str:
        """
        Форматирует сообщение о создании заказа
        
        Args:
            order: Объект Order из БД
            
        Returns:
            Отформатированное сообщение
        """
        from datetime import datetime
        
        # Форматируем дату создания
        if order.created_at:
            created_date = order.created_at.strftime("%d.%m.%Y %H:%M")
        else:
            created_date = "не указана"
        
        # Получаем имя исполнителя
        executor_name = order.executor.username if order.executor else "Не указан"
        
        # Подсчитываем количество продуктов
        total_products = len(order.products) if order.products else 0
        
        # Формируем сообщение
        message = f"📦 <b>Создан новый заказ #{order.id}</b>\n\n"
        message += f"Исполнитель: {executor_name}\n"
        message += f"Дата создания: {created_date}\n"
        message += f"Количество продуктов: {total_products}\n"
        
        # Добавляем список продуктов, если их немного (до 5)
        if order.products and len(order.products) <= 5:
            message += "\n<b>Продукты:</b>\n"
            for product in order.products:
                product_line = f"• {product.name}"
                if product.quantity > 1:
                    product_line += f" (x{product.quantity})"
                if product.notes:
                    product_line += f" - {product.notes}"
                message += product_line + "\n"
        elif order.products and len(order.products) > 5:
            message += f"\n(Список из {len(order.products)} продуктов доступен в приложении)"
        
        return message
    
    def format_order_completed_message(self, order) -> str:
        """
        Форматирует сообщение о завершении заказа
        
        Args:
            order: Объект Order из БД
            
        Returns:
            Отформатированное сообщение
        """
        from datetime import datetime
        
        # Форматируем дату завершения
        if order.completed_at:
            completed_date = order.completed_at.strftime("%d.%m.%Y %H:%M")
        else:
            completed_date = "не указана"
        
        # Получаем имя исполнителя
        executor_name = order.executor.username if order.executor else "Не указан"
        
        # Формируем сообщение
        message = f"✅ <b>Заказ #{order.id} завершен</b>\n\n"
        message += f"Исполнитель: {executor_name}\n"
        message += f"Дата завершения: {completed_date}\n"
        
        # Добавляем комментарий, если есть
        if order.complete_comment:
            message += f"\nКомментарий исполнителя:\n{order.complete_comment}"
        
        return message
    
    def send_order_created_notification(self, order, db) -> bool:
        """
        Отправляет уведомление о создании заказа заказчику
        
        Args:
            order: Объект Order из БД
            db: Сессия базы данных
            
        Returns:
            True если уведомление отправлено, False в противном случае
        """
        from notifications.crud import notification_crud
        
        # Получаем настройки уведомлений заказчика
        settings_obj = notification_crud.get_notification_settings(db, order.customer_id)
        
        # Проверяем, включены ли уведомления
        if not settings_obj or not settings_obj.telegram_enabled:
            logger.debug(f"Уведомления отключены для пользователя {order.customer_id}")
            return False
        
        if not settings_obj.notify_order_completed:
            # Используем ту же настройку, что и для завершения заказа
            # Если пользователь хочет получать уведомления о завершении, логично получать и о создании
            logger.debug(f"Уведомления о заказах отключены для пользователя {order.customer_id}")
            return False
        
        # Проверяем, есть ли у заказчика привязанный Telegram
        if not order.customer.telegram_id:
            logger.debug(f"У пользователя {order.customer_id} не привязан Telegram")
            return False
        
        # Форматируем и отправляем сообщение
        message = self.format_order_created_message(order)
        return self.send_message(order.customer.telegram_id, message)
    
    def send_order_completed_notification(self, order, db) -> bool:
        """
        Отправляет уведомление о завершении заказа заказчику
        
        Args:
            order: Объект Order из БД
            db: Сессия базы данных
            
        Returns:
            True если уведомление отправлено, False в противном случае
        """
        from notifications.crud import notification_crud
        
        # Получаем настройки уведомлений заказчика
        settings_obj = notification_crud.get_notification_settings(db, order.customer_id)
        
        # Проверяем, включены ли уведомления
        if not settings_obj or not settings_obj.telegram_enabled:
            logger.debug(f"Уведомления отключены для пользователя {order.customer_id}")
            return False
        
        if not settings_obj.notify_order_completed:
            logger.debug(f"Уведомления о завершении заказа отключены для пользователя {order.customer_id}")
            return False
        
        # Проверяем, есть ли у заказчика привязанный Telegram
        if not order.customer.telegram_id:
            logger.debug(f"У пользователя {order.customer_id} не привязан Telegram")
            return False
        
        # Форматируем и отправляем сообщение
        message = self.format_order_completed_message(order)
        return self.send_message(order.customer.telegram_id, message)
    
    def get_chat(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о чате (для проверки существования пользователя)
        
        Args:
            telegram_id: Telegram ID пользователя
            
        Returns:
            Информация о чате или None в случае ошибки
        """
        params = {"chat_id": telegram_id}
        return self._make_request("getChat", params)

