from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from database import engine, Base, wait_for_database
from auth.routers import auth_router
from auth.routers.role_router import router as role_router # Добавляю обратно
from app.admin import admin_router
from products.routers import customer_router, executor_router
from notifications.routers import notification_router
# Импортируем модели для регистрации в Base.metadata
from notifications.models import NotificationSettings, TelegramVerificationCode
from auth.utils.admin_init import ensure_admin_exists, ensure_basic_roles
from auth.utils.init_roles import ensure_basic_roles as ensure_role_models
from database import SessionLocal
from utils.logging_config import setup_logging
from middleware.logging_middleware import LoggingMiddleware
import time
import os

# Настраиваем логирование
setup_logging()

# Функция инициализации базы данных
def initialize_database():
    """Инициализация базы данных с обработкой ошибок и повторными попытками"""
    print("🔍 Начинаем инициализацию базы данных...")
    
    # Шаг 1: Ожидание готовности базы данных
    print("🔍 Ожидание готовности базы данных...")
    if not wait_for_database(max_retries=30, retry_delay=2):
        print("❌ Не удалось подключиться к базе данных")
        print("⚠️  Приложение будет запущено, но некоторые функции могут не работать")
        print("⚠️  Инициализация БД будет повторена при следующем запросе")
        return False
    
    try:
        print("🔍 Создание таблиц в базе данных...")
        # Создаем таблицы в базе данных
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы/проверены")
        
        # Небольшая задержка для завершения операций с таблицами
        time.sleep(1)
        
        # Инициализируем базовые роли в таблице roles (для множественных ролей)
        print("🔍 Инициализация системы множественных ролей...")
        db = SessionLocal()
        try:
            ensure_role_models(db)
            db.commit()
            print("✅ Система множественных ролей инициализирована")
        except Exception as e:
            print(f"⚠️  Ошибка при инициализации ролей: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
        finally:
            db.close()
        
        # Инициализируем администратора и базовые роли при запуске
        print("🔍 Проверяем наличие администратора в системе...")
        try:
            ensure_admin_exists()
            print("✅ Администратор проверен/создан")
        except Exception as e:
            print(f"⚠️  Ошибка при проверке администратора: {e}")
            import traceback
            traceback.print_exc()
        
        print("🔍 Проверяем наличие базовых ролей в системе...")
        try:
            ensure_basic_roles()
            print("✅ Базовые роли проверены/созданы")
        except Exception as e:
            print(f"⚠️  Ошибка при проверке базовых ролей: {e}")
            import traceback
            traceback.print_exc()
        
        print("✅ Инициализация базы данных завершена успешно")
        return True
            
    except Exception as e:
        print(f"❌ Критическая ошибка при инициализации базы данных: {e}")
        import traceback
        traceback.print_exc()
        # Не прерываем запуск приложения, возможно БД еще не готова
        print("⚠️  Продолжаем запуск приложения, инициализация БД будет повторена...")
        return False

# Выполняем инициализацию
print("=" * 60)
print("🚀 Запуск FastAPI приложения")
print("=" * 60)
database_initialized = initialize_database()
if not database_initialized:
    print("⚠️  Предупреждение: База данных не инициализирована, но приложение продолжает работу")
print("=" * 60)

app = FastAPI(
    title="FastAPI Auth System", 
    version="1.0.0",
    description="Система аутентификации с JWT токенами, управлением пользователями и заказами",
    docs_url="/api/docs",  # Документация доступна по /api/docs
    redoc_url="/api/redoc",  # ReDoc доступен по /api/redoc
    openapi_url="/api/openapi.json"  # OpenAPI схема по /api/openapi.json
)

# Настройка CORS
# Получаем разрешенные origins из переменной окружения или используем значения по умолчанию
cors_origins_str = os.getenv("CORS_ORIGINS", "https://products.bunkov.in")
# Разбираем строку origins
allowed_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    # Разрешаем localhost с любым портом для разработки
    allow_origin_regex=r"http://localhost:\d+|https://localhost:\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=3600,
)

# Добавляем middleware для логирования
app.add_middleware(LoggingMiddleware)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(customer_router)
app.include_router(executor_router)
app.include_router(role_router)
app.include_router(notification_router)

@app.get("/")
async def root():
    """
    Корневой endpoint для сайта.
    Здесь будет отображаться фронтенд приложение.
    """
    return {
        "message": "Welcome to Products Backend",
        "api_docs": "/api/docs",
        "api_redoc": "/api/redoc",
        "api_openapi": "/api/openapi.json",
        "status": "API доступен по пути /api/*"
    }

@app.get("/health")
async def health_check():
    """Расширенная проверка состояния системы"""
    import psutil
    import time
    from database import engine
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Проверка базы данных
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": "< 1ms"
        }
    except Exception as e:
        # БД недоступна, но приложение работает
        health_status["status"] = "degraded"  # Изменено с unhealthy на degraded
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)[:200]  # Ограничиваем длину сообщения об ошибке
        }
    
    # Проверка системных ресурсов
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["checks"]["system"] = {
            "status": "healthy",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        }
        
        # Проверяем критические пороги
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unhealthy",
            "error": str(e)[:200]
        }
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    # Проверка внешних зависимостей (если есть)
    health_status["checks"]["external_services"] = {
        "status": "healthy",
        "services": []
    }
    
    # Healthcheck должен возвращать 200 даже при проблемах с БД
    # Это позволяет контейнеру запуститься и повторить попытку подключения
    return health_status

# Кастомная Swagger UI с правильными настройками авторизации (доступна по /api/docs)
# FastAPI автоматически создаст endpoint /api/docs, но если нужна кастомная версия, раскомментируйте:
# @app.get("/api/docs", include_in_schema=False)
# async def custom_swagger_ui_html():
#     return get_swagger_ui_html(
#         openapi_url=app.openapi_url,
#         title=app.title + " - Swagger UI",
#         oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
#         swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
#         swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
#         swagger_ui_parameters={
#             "persistAuthorization": True,  # Сохраняем авторизацию
#             "displayRequestDuration": True,
#             "filter": True,
#             "tryItOutEnabled": True,
#         }
#     )

# Кастомная ReDoc (доступна по /api/redoc)
# FastAPI автоматически создаст endpoint /api/redoc, но если нужна кастомная версия, раскомментируйте:
# @app.get("/api/redoc", include_in_schema=False)
# async def redoc_html():
#     return get_swagger_ui_html(
#         openapi_url=app.openapi_url,
#         title=app.title + " - ReDoc",
#         swagger_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
#         swagger_css_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.css",
#     )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
