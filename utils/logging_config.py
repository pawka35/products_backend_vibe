import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from config import settings

class JSONFormatter(logging.Formatter):
    """Форматтер для структурированного JSON логирования"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Добавляем дополнительные поля если они есть
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        
        # Добавляем исключение если есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

class SecurityLogger:
    """Логгер для событий безопасности"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Добавляем обработчик для файла безопасности
        security_handler = logging.FileHandler('logs/security.log')
        security_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(security_handler)
    
    def log_login_attempt(self, username: str, ip_address: str, success: bool, user_id: Optional[int] = None):
        """Логирование попытки входа"""
        extra = {
            'user_id': user_id,
            'ip_address': ip_address,
            'event_type': 'login_attempt',
            'username': username,
            'success': success
        }
        
        if success:
            self.logger.info(f"Успешный вход пользователя {username}", extra=extra)
        else:
            self.logger.warning(f"Неудачная попытка входа пользователя {username}", extra=extra)
    
    def log_password_change(self, user_id: int, changed_by: int, ip_address: str):
        """Логирование изменения пароля"""
        extra = {
            'user_id': user_id,
            'changed_by': changed_by,
            'ip_address': ip_address,
            'event_type': 'password_change'
        }
        self.logger.info(f"Изменение пароля пользователя {user_id}", extra=extra)
    
    def log_role_change(self, user_id: int, old_role: str, new_role: str, changed_by: int, ip_address: str):
        """Логирование изменения роли"""
        extra = {
            'user_id': user_id,
            'old_role': old_role,
            'new_role': new_role,
            'changed_by': changed_by,
            'ip_address': ip_address,
            'event_type': 'role_change'
        }
        self.logger.info(f"Изменение роли пользователя {user_id} с {old_role} на {new_role}", extra=extra)
    
    def log_suspicious_activity(self, description: str, ip_address: str, user_id: Optional[int] = None):
        """Логирование подозрительной активности"""
        extra = {
            'user_id': user_id,
            'ip_address': ip_address,
            'event_type': 'suspicious_activity'
        }
        self.logger.warning(f"Подозрительная активность: {description}", extra=extra)

class APILogger:
    """Логгер для API запросов"""
    
    def __init__(self):
        self.logger = logging.getLogger('api')
        self.logger.setLevel(logging.INFO)
        
        # Добавляем обработчик для файла API
        api_handler = logging.FileHandler('logs/api.log')
        api_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(api_handler)
    
    def log_request(self, method: str, endpoint: str, user_id: Optional[int], 
                   ip_address: str, execution_time: float, status_code: int):
        """Логирование API запроса"""
        extra = {
            'user_id': user_id,
            'ip_address': ip_address,
            'endpoint': f"{method} {endpoint}",
            'execution_time': execution_time,
            'status_code': status_code,
            'event_type': 'api_request'
        }
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        self.logger.log(level, f"API запрос {method} {endpoint}", extra=extra)

class BusinessLogger:
    """Логгер для бизнес-событий"""
    
    def __init__(self):
        self.logger = logging.getLogger('business')
        self.logger.setLevel(logging.INFO)
        
        # Добавляем обработчик для файла бизнес-событий
        business_handler = logging.FileHandler('logs/business.log')
        business_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(business_handler)
    
    def log_order_created(self, order_id: int, customer_id: int, executor_id: int):
        """Логирование создания заказа"""
        extra = {
            'order_id': order_id,
            'customer_id': customer_id,
            'executor_id': executor_id,
            'event_type': 'order_created'
        }
        self.logger.info(f"Создан заказ {order_id}", extra=extra)
    
    def log_order_completed(self, order_id: int, executor_id: int):
        """Логирование завершения заказа"""
        extra = {
            'order_id': order_id,
            'executor_id': executor_id,
            'event_type': 'order_completed'
        }
        self.logger.info(f"Завершен заказ {order_id}", extra=extra)
    
    def log_user_registration(self, user_id: int, username: str, role: str):
        """Логирование регистрации пользователя"""
        extra = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'event_type': 'user_registration'
        }
        self.logger.info(f"Зарегистрирован пользователь {username}", extra=extra)

def setup_logging():
    """Настройка системы логирования"""
    import os
    
    # Создаем директорию для логов
    os.makedirs('logs', exist_ok=True)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Удаляем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Добавляем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == 'json':
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    root_logger.addHandler(console_handler)
    
    # Добавляем обработчик для файла
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Создаем специализированные логгеры
    security_logger = SecurityLogger()
    api_logger = APILogger()
    business_logger = BusinessLogger()
    
    return security_logger, api_logger, business_logger

# Глобальные экземпляры логгеров
security_logger, api_logger, business_logger = setup_logging()
