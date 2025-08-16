# Application Package

Модуль для управления пользователями и административных функций в системе FastAPI.

## Структура

```
app/
├── __init__.py
├── models/           # Модели данных (пусто)
├── schemas/          # Pydantic схемы
│   ├── __init__.py
│   └── admin_schemas.py
├── crud/            # CRUD операции
│   ├── __init__.py
│   └── admin_crud.py
├── routers/         # FastAPI роутеры
│   ├── __init__.py
│   └── users.py
├── admin/           # Административные функции
│   ├── __init__.py
│   └── admin_router.py
├── tests/           # Тесты
│   ├── __init__.py
│   ├── test_api.py
│   └── test_admin.py
└── README.md
```

## Функционал

### 👥 Управление пользователями
- Просмотр списка пользователей
- Получение пользователя по ID
- Фильтрация пользователей по ролям

### 🔴 Административные функции
- Изменение паролей пользователей
- Изменение ролей пользователей
- Деактивация пользователей
- Статистика по пользователям
- Массовые операции

## API Endpoints

### Пользователи (требует авторизации)
- `GET /users/` - список всех пользователей
- `GET /users/{user_id}` - пользователь по ID
- `GET /users/role/{role}` - пользователи по роли

### Администратор (требует роль admin)
- `GET /admin/users` - список всех пользователей
- `GET /admin/users/{user_id}` - пользователь по ID
- `PUT /admin/users/{user_id}/password` - изменение пароля
- `PUT /admin/users/{user_id}/role` - изменение роли
- `DELETE /admin/users/{user_id}` - деактивация пользователя
- `GET /admin/users/role/{role}` - пользователи по роли
- `GET /admin/statistics` - статистика пользователей
- `POST /admin/users/bulk/change-role` - массовое изменение ролей

## Использование

```python
# Импорт роутеров
from app.routers import users_router
from app.admin import admin_router

# Подключение к FastAPI приложению
app.include_router(users_router)
app.include_router(admin_router)
```

## Тестирование

```bash
# Запуск теста API
python app/tests/test_api.py

# Запуск теста административных функций
python app/tests/test_admin.py

# Или через общий скрипт
python run_tests.py api
python run_tests.py admin
```

## Зависимости

- FastAPI
- SQLAlchemy
- Pydantic
- Python 3.8+
