import os
import secrets
import string
from dotenv import load_dotenv

load_dotenv()

def generate_secure_secret(length: int = 32) -> str:
    """Генерирует криптографически стойкий секретный ключ"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_or_create_secret_key() -> str:
    """Получает секретный ключ из переменной окружения или создает новый"""
    secret_key = os.getenv("SECRET_KEY")
    
    if not secret_key or secret_key == "your-secret-key-here-change-in-production":
        # Генерируем новый секрет
        new_secret = generate_secure_secret(64)
        print(f"⚠️  ВНИМАНИЕ: Сгенерирован новый SECRET_KEY: {new_secret}")
        print("⚠️  Сохраните этот ключ в переменной окружения SECRET_KEY для продакшена!")
        return new_secret
    
    return secret_key

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://fastapi_user:fastapi_password@localhost:3307/fastapi_auth")
    SECRET_KEY: str = get_or_create_secret_key()
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Настройки безопасности
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_MAX_LENGTH: int = int(os.getenv("PASSWORD_MAX_LENGTH", "128"))
    
    # Настройки rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # секунды
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")

settings = Settings()
