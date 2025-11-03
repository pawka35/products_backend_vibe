# 🏠 Основное приложение

Основной модуль FastAPI приложения, содержащий административные функции, управление пользователями и общие API endpoints.

## 🚀 Основные возможности

### 👥 Управление пользователями
- **CRUD операции** с пользователями
- **Фильтрация по ролям** и статусам
- **Административные функции** управления пользователями
- **Статистика пользователей** системы

### 🔐 Административные функции
- **Управление ролями** пользователей
- **Изменение паролей** пользователей
- **Статистика системы** и мониторинг
- **Доступ только для администраторов**

### 🌐 Общие API endpoints
- **Health check** для мониторинга
- **Главная страница** с информацией о системе
- **Документация API** (Swagger/ReDoc)

## 🏗️ Архитектура

```
app/
├── admin/                 # Административные функции
│   ├── admin_router.py   # Роутер административных функций
│   └── admin_crud.py     # CRUD операции для админа
├── crud/                  # CRUD операции
│   └── admin_crud.py     # Операции с пользователями
├── models/                # Модели данных
│   └── __init__.py       # Инициализация моделей
├── routers/               # API роутеры
│   └── users.py          # Роутер пользователей
├── schemas/               # Pydantic схемы
│   └── admin_schemas.py  # Схемы административных функций
├── tests/                 # Тесты
│   ├── test_admin.py     # Тесты административных функций
│   └── test_api.py       # Тесты API
└── README.md              # Документация
```

## 📚 API Endpoints

### Основные
- `GET /` - Главная страница с информацией о системе
- `GET /health` - Проверка здоровья сервиса
- `GET /docs` - Swagger документация API
- `GET /redoc` - ReDoc документация API

### Пользователи
- `GET /users/` - Список всех пользователей
- `GET /users/{id}` - Информация о конкретном пользователе
- `GET /users/role/{role}` - Пользователи с определенной ролью

### Административные функции (только для администраторов)
- `POST /admin/users` - Создание нового пользователя (с любой ролью, включая admin)
- `GET /admin/statistics` - Статистика пользователей системы
- `GET /admin/users` - Список всех пользователей для администратора
- `GET /admin/users/{id}` - Детальная информация о пользователе
- `GET /admin/users/role/{role}` - Пользователи с определенной ролью
- `PUT /admin/users/{id}/role` - Изменение роли пользователя
- `PUT /admin/users/{id}/password` - Изменение пароля пользователя
- `DELETE /admin/users/{id}` - Деактивация пользователя

## 🔒 Модели данных

### User (Пользователь)
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### UserRole (Роль пользователя)
```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"        # Администратор системы
    CUSTOMER = "customer"  # Заказчик
    EXECUTOR = "executor"  # Исполнитель заказов
```

## 📊 Статистика системы

### AdminStatisticsResponse
```python
class AdminStatisticsResponse(BaseModel):
    total_users: int
    users_by_role: Dict[str, int]
    active_users: int
    inactive_users: int
    system_info: Dict[str, Any]
```

### Пример ответа
```json
{
    "total_users": 10,
    "users_by_role": {
        "admin": 1,
        "customer": 7,
        "executor": 2
    },
    "active_users": 9,
    "inactive_users": 1,
    "system_info": {
        "version": "1.0.0",
        "uptime": "2h 30m"
    }
}
```

## 🔐 Авторизация

### Требования к доступу
- **Основные endpoints** (`/`, `/health`, `/docs`) - доступны всем
- **Пользовательские endpoints** (`/users/*`) - требуют аутентификации
- **Административные endpoints** (`/admin/*`) - требуют роль администратора

### Проверка прав доступа
```python
from auth.utils.admin_auth import get_current_admin_user

@router.get("/admin/statistics")
async def get_statistics(
    current_user: User = Depends(get_current_admin_user)
):
    """Получение статистики (только для администраторов)"""
    # Логика получения статистики
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Тесты административных функций
python app/tests/test_admin.py

# Тесты API
python app/tests/test_api.py

# Все тесты модуля
python -m pytest app/tests/ -v
```

### Покрытие тестами
- ✅ Основные API endpoints
- ✅ Административные функции
- ✅ Управление пользователями
- ✅ Проверка авторизации
- ✅ Статистика системы

## 📊 Примеры использования

### Создание пользователя администратором
```python
# POST /admin/users
# Headers: Authorization: Bearer <admin_token>
{
    "username": "new_user",
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "role": "customer"  # или "executor", или "admin"
}

# Ответ
{
    "id": 10,
    "username": "new_user",
    "email": "newuser@example.com",
    "role": "customer",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": null
}
```

**Особенности:**
- ✅ Администратор может создавать пользователей с любой ролью, включая `admin`
- ✅ Пароль должен соответствовать требованиям безопасности (минимум 8 символов)
- ✅ Username и email должны быть уникальными
- ✅ Валидация данных происходит на уровне схемы

### Получение статистики
```python
# GET /admin/statistics
# Headers: Authorization: Bearer <admin_token>

# Ответ
{
    "total_users": 10,
    "users_by_role": {
        "admin": 1,
        "customer": 7,
        "executor": 2
    },
    "active_users": 9,
    "inactive_users": 1
}
```

### Изменение роли пользователя
```python
# PUT /admin/users/5/role
# Headers: Authorization: Bearer <admin_token>
{
    "role": "executor"
}

# Ответ
{
    "id": 5,
    "username": "testuser",
    "role": "executor",
    "message": "Роль пользователя изменена"
}
```

### Изменение пароля пользователя
```python
# PUT /admin/users/5/password
# Headers: Authorization: Bearer <admin_token>
{
    "new_password": "newSecurePassword123"
}

# Ответ
{
    "id": 5,
    "username": "testuser",
    "message": "Пароль пользователя изменен"
}
```

## 🔧 Настройка

### Переменные окружения
```bash
# Настройки приложения
APP_NAME=FastAPI Backend System
APP_VERSION=1.0.0
DEBUG=false

# Настройки безопасности
ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_USERNAME=admin
```

### Конфигурация FastAPI
```python
app = FastAPI(
    title="FastAPI Backend System",
    description="Полнофункциональная система управления пользователями и заказами",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

## 📝 Логирование

### Уровни логирования
- **INFO** - основные операции (создание, обновление, удаление)
- **WARNING** - потенциальные проблемы
- **ERROR** - ошибки и исключения
- **DEBUG** - детальная информация для отладки

### Логируемые события
- **Управление пользователями** - все CRUD операции
- **Изменения ролей** - кто, когда, какую роль изменил
- **Изменения паролей** - административные изменения
- **Доступ к защищенным endpoints** - попытки несанкционированного доступа

## 🚨 Ограничения

### Безопасность
- **Только администраторы** могут изменять роли и пароли
- **Нельзя изменить** роль администратора у самого себя
- **Пароли должны соответствовать** политике безопасности

### Функциональность
- **Нельзя удалить** последнего администратора
- **Нельзя деактивировать** системные роли
- **Ограничения на количество** пользователей в системе

## 🔄 Миграции

### Добавление новых полей
1. Обновить модель в `models/`
2. Обновить схему в `schemas/`
3. Обновить CRUD операции
4. Запустить миграцию базы данных

### Добавление новых ролей
1. Добавить в enum `UserRole`
2. Обновить логику авторизации
3. Обновить тесты

## 📈 Мониторинг

### Health Check
- **Проверка базы данных** - подключение и основные запросы
- **Проверка внешних сервисов** - доступность API
- **Проверка системных ресурсов** - память, диск, CPU

### Метрики
- **Количество пользователей** по ролям
- **Активность пользователей** - входы, операции
- **Время ответа** API endpoints
- **Ошибки и исключения** в системе

## 🔒 Безопасность

### Аутентификация
- **JWT токены** для безопасной аутентификации
- **Хеширование паролей** с bcrypt
- **Валидация входных данных** с Pydantic

### Авторизация
- **Ролевая система** (RBAC)
- **Проверка прав доступа** на уровне endpoints
- **Аудит административных операций**

## 🤝 Интеграция

### С другими модулями
- **auth** - аутентификация и управление ролями
- **products** - управление заказами и поиск
- **database** - подключение к базе данных

### Внешние зависимости
- **MySQL** - база данных
- **Redis** - кэширование (опционально)
- **Logging** - система логирования

---

**Модуль готов к использованию в продакшене! 🚀**
