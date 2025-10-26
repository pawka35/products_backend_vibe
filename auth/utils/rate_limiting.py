from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from config import settings
import redis
from typing import Optional

# Инициализация Redis (опционально)
redis_client: Optional[redis.Redis] = None

try:
    redis_url = settings.DATABASE_URL.replace("mysql+pymysql://", "redis://").replace("fastapi_auth", "0")
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()  # Проверяем подключение
except Exception:
    redis_client = None

# Инициализация лимитера
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379" if redis_client else "memory://",
    default_limits=[f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}second"]
)

def get_rate_limit_key(request: Request) -> str:
    """Получает ключ для rate limiting на основе IP и пользователя"""
    # Если пользователь авторизован, используем его ID
    if hasattr(request.state, 'user') and request.state.user:
        return f"user:{request.state.user.id}"
    
    # Иначе используем IP адрес
    return get_remote_address(request)

# Специальные лимиты для разных endpoint'ов
login_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379" if redis_client else "memory://",
    default_limits=["5/1minute"]  # 5 попыток входа в минуту
)

register_limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379" if redis_client else "memory://",
    default_limits=["3/1minute"]  # 3 регистрации в минуту
)

admin_limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri="redis://localhost:6379" if redis_client else "memory://",
    default_limits=["1000/1hour"]  # 1000 запросов в час для админов
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Обработчик превышения лимита запросов"""
    response = HTTPException(
        status_code=429,
        detail=f"Превышен лимит запросов: {exc.detail}"
    )
    return response

# Декораторы для удобного использования
def rate_limit(limit: str):
    """Декоратор для применения rate limiting"""
    return limiter.limit(limit)

def login_rate_limit(limit: str = "5/1minute"):
    """Декоратор для rate limiting на endpoint'ах входа"""
    return login_limiter.limit(limit)

def register_rate_limit(limit: str = "3/1minute"):
    """Декоратор для rate limiting на endpoint'ах регистрации"""
    return register_limiter.limit(limit)

def admin_rate_limit(limit: str = "1000/1hour"):
    """Декоратор для rate limiting на админских endpoint'ах"""
    return admin_limiter.limit(limit)
