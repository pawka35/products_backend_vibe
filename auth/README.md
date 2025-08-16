# Authentication Package

Модуль для аутентификации и управления пользователями в системе FastAPI.

## Структура

```
auth/
├── __init__.py
├── models/           # Модели данных
│   ├── __init__.py
│   └── user_models.py
├── schemas/          # Pydantic схемы
│   ├── __init__.py
│   └── user_schemas.py
├── crud/            # CRUD операции
│   ├── __init__.py
│   └── user_crud.py
├── routers/         # FastAPI роутеры
│   ├── __init__.py
│   └── auth_router.py
├── utils/           # Утилиты
│   ├── __init__.py
│   └── auth_utils.py
├── tests/           # Тесты
│   ├── __init__.py
│   └── test_auth.py
└── README.md
```

## Функционал

### 🔐 Аутентификация
- Регистрация пользователей
- JWT токены для входа
- Проверка текущего пользователя

### 👥 Управление пользователями
- CRUD операции для пользователей
- Хеширование паролей
- Проверка аутентификации

## Модели данных

### User (Пользователь)
- `id` - уникальный идентификатор
- `username` - имя пользователя
- `email` - электронная почта
- `hashed_password` - хешированный пароль
- `role` - роль пользователя (admin, customer, executor)
- `created_at` - время создания
- `updated_at` - время обновления

## API Endpoints

### Аутентификация
- `POST /auth/register` - регистрация пользователя
- `POST /auth/token` - получение JWT токена
- `GET /auth/me` - информация о текущем пользователе

## Использование

```python
# Импорт роутера
from auth.routers import auth_router

# Подключение к FastAPI приложению
app.include_router(auth_router)
```

## Тестирование

```bash
# Запуск теста аутентификации
python auth/tests/test_auth.py

# Или через общий скрипт
python run_tests.py auth
```

## Зависимости

- FastAPI
- SQLAlchemy
- Pydantic
- Python-Jose (JWT)
- Passlib (хеширование паролей)
- Python 3.8+
