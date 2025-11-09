from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from config import settings
import time

# Создаем engine с параметрами для обработки проблем подключения
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверяет соединение перед использованием
    pool_recycle=3600,   # Переиспользует соединения каждые 3600 секунд
    connect_args={
        "connect_timeout": 10,  # Таймаут подключения 10 секунд
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_database(max_retries=30, retry_delay=2):
    """
    Ожидание готовности базы данных с повторными попытками подключения
    """
    from sqlalchemy import text
    for attempt in range(max_retries):
        try:
            # Пытаемся подключиться к базе данных
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Подключение к базе данных успешно (попытка {attempt + 1})")
            return True
        except OperationalError as e:
            error_msg = str(e)
            # Не выводим сообщение на каждой попытке, только на каждой 5-й
            if attempt % 5 == 0 or attempt == max_retries - 1:
                print(f"⚠️  Попытка подключения к БД {attempt + 1}/{max_retries}: {error_msg[:100]}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"❌ Не удалось подключиться к базе данных после {max_retries} попыток")
                return False
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Неожиданная ошибка при подключении к БД: {error_msg[:200]}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return False
    return False
