import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from utils.logging_config import api_logger
from typing import Optional

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования API запросов"""
    
    async def dispatch(self, request: Request, call_next):
        # Генерируем уникальный ID для запроса
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Получаем IP адрес
        ip_address = request.client.host if request.client else "unknown"
        request.state.ip_address = ip_address
        
        # Получаем информацию о пользователе если есть
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.id
        
        # Засекаем время начала обработки
        start_time = time.time()
        
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Вычисляем время выполнения
        execution_time = time.time() - start_time
        
        # Логируем запрос
        api_logger.log_request(
            method=request.method,
            endpoint=str(request.url.path),
            user_id=user_id,
            ip_address=ip_address,
            execution_time=execution_time,
            status_code=response.status_code
        )
        
        # Добавляем request_id в заголовки ответа
        response.headers["X-Request-ID"] = request_id
        
        return response
