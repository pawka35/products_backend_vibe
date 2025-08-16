from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from database import engine, Base
from auth.routers import auth_router
from auth.routers.role_router import router as role_router
from app.routers import users_router
from app.admin import admin_router
from products.routers import orders_router, executor_router, search_router
from auth.utils.admin_init import ensure_admin_exists

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Инициализируем администратора при запуске
print("🔍 Проверяем наличие администратора в системе...")
ensure_admin_exists()

app = FastAPI(
    title="FastAPI Auth System", 
    version="1.0.0",
    description="Система аутентификации с JWT токенами, управлением пользователями и заказами",
    docs_url=None,  # Отключаем стандартную документацию
    redoc_url=None  # Отключаем стандартную документацию
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(orders_router)
app.include_router(executor_router)
app.include_router(search_router)
app.include_router(role_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI Auth System",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Кастомная Swagger UI с правильными настройками авторизации
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters={
            "persistAuthorization": True,  # Сохраняем авторизацию
            "displayRequestDuration": True,
            "filter": True,
            "tryItOutEnabled": True,
        }
    )

# Кастомная ReDoc
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        swagger_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.css",
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
