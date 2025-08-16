# 🔐 Модуль аутентификации и авторизации

Полнофункциональная система аутентификации, авторизации и управления ролями для FastAPI приложения.

## 🚀 Основные возможности

### 🔑 Аутентификация
- **Регистрация пользователей** с валидацией данных
- **JWT токены** для безопасной аутентификации
- **Хеширование паролей** с bcrypt
- **Защита от создания администраторов** через регистрацию

### 🎭 Управление ролями (RBAC)
- **Создание и управление ролями** (только для администраторов)
- **Назначение ролей пользователям**
- **Гибкая система ролей**: базовые + дополнительные
- **Удаление ролей у пользователей**

### 👥 Управление пользователями
- **CRUD операции** с пользователями
- **Ролевая система**: admin, customer, executor
- **Административные функции** управления пользователями
- **Автоматическая инициализация** первого администратора

## 🏗️ Архитектура

```
auth/
├── crud/              # CRUD операции
│   ├── user_crud.py   # Операции с пользователями
│   └── role_crud.py   # Операции с ролями
├── models/            # SQLAlchemy модели
│   ├── user_models.py # Модели пользователей
│   └── role_models.py # Модели ролей
├── routers/           # API роутеры
│   ├── auth_router.py # Аутентификация
│   └── role_router.py # Управление ролями
├── schemas/           # Pydantic схемы
│   ├── user_schemas.py # Схемы пользователей
│   └── role_schemas.py # Схемы ролей
├── tests/             # Тесты
│   ├── test_auth.py   # Тесты аутентификации
│   ├── test_roles.py  # Тесты ролей
│   └── test_admin_init.py # Тесты инициализации
├── utils/             # Утилиты
│   ├── auth_utils.py  # Утилиты аутентификации
│   └── admin_init.py  # Инициализация администратора
└── README.md          # Документация
```

## 📚 API Endpoints

### Аутентификация
- `POST /auth/register` - Регистрация пользователя
- `POST /auth/token` - Получение JWT токена
- `GET /auth/me` - Информация о текущем пользователе

### Управление ролями (только для администраторов)
- `GET /admin/roles` - Список всех ролей
- `POST /admin/roles` - Создание новой роли
- `GET /admin/roles/{id}` - Получение роли по ID
- `PUT /admin/roles/{id}` - Обновление роли
- `DELETE /admin/roles/{id}` - Удаление роли
- `POST /admin/roles/{id}/activate` - Активация роли

### Управление назначениями ролей
- `GET /admin/roles/users/{id}` - Роли пользователя
- `GET /admin/roles/{id}/users` - Пользователи с ролью
- `POST /admin/roles/users/assign` - Назначение роли пользователю
- `PUT /admin/roles/users/{id}` - Обновление роли пользователя
- `DELETE /admin/roles/users/{id}` - Удаление роли у пользователя

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

### Role (Роль)
```python
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### RoleAssignment (Назначение роли)
```python
class RoleAssignment(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
```

## 🎯 Система ролей

### Базовые роли (enum UserRole)
- **ADMIN** - Полный доступ к системе
- **CUSTOMER** - Создание и управление заказами
- **EXECUTOR** - Исполнение заказов

### Дополнительные роли
- Создаются администраторами
- Назначаются пользователям дополнительно к базовой роли
- Пример: moderator, manager, supervisor

### Логика работы
1. **Базовая роль** - хранится в таблице `users.role`
2. **Дополнительные роли** - хранятся в таблице `user_roles`
3. **Эндпоинт `/admin/roles/users/{id}`** показывает все роли пользователя

## 🔐 Безопасность

### Защита от создания администраторов
- Валидатор в `UserBase` и `UserUpdate` схемах
- Проверка в `/auth/register` эндпоинте
- Только автоматическая инициализация первого администратора

### JWT токены
- Алгоритм: HS256
- Настраиваемое время жизни
- Безопасное хранение в заголовках

### Хеширование паролей
- bcrypt с солью
- Безопасное хранение в базе данных

## 🚀 Инициализация системы

### Автоматическое создание администратора
```python
# При запуске приложения
ensure_admin_exists()  # Создает 'admin' пользователя если не существует
ensure_basic_roles()   # Создает базовые роли: admin, customer, executor
```

### Первый администратор
- **Username**: admin
- **Email**: user@example.com
- **Пароль**: генерируется случайно и выводится в консоль
- **Роль**: admin

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты аутентификации
python auth/tests/test_auth.py

# Тесты управления ролями
python auth/tests/test_roles.py

# Тесты инициализации администратора
python auth/tests/test_admin_init.py
```

### Покрытие тестами
- ✅ Регистрация и аутентификация
- ✅ Управление ролями
- ✅ CRUD операции
- ✅ Проверка разрешений
- ✅ Инициализация системы

## 📊 Примеры использования

### Создание роли
```python
# POST /admin/roles/
{
    "name": "moderator",
    "description": "Роль модератора",
    "permissions": "read,write,moderate"
}
```

### Назначение роли пользователю
```python
# POST /admin/roles/users/assign
{
    "user_id": 1,
    "role_id": 4
}
```

### Получение ролей пользователя
```python
# GET /admin/roles/users/1
[
    {
        "role_name": "customer",
        "role_type": "base",
        "is_active": true
    },
    {
        "role_name": "moderator",
        "role_type": "additional",
        "is_active": true
    }
]
```

## 🔧 Настройка

### Переменные окружения
```bash
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### База данных
- MySQL 8.0+
- Автоматическое создание таблиц
- Миграции через SQLAlchemy

## 📝 Логирование

- Все операции с ролями логируются
- Ошибки аутентификации отслеживаются
- Аудит назначений ролей

## 🚨 Ограничения

- **Только администраторы** могут управлять ролями
- **Нельзя удалить** системную роль 'admin' у пользователя
- **Нельзя создать** администратора через регистрацию
- **Мягкое удаление** ролей (деактивация)

## 🔄 Миграции

### Добавление новых полей
1. Обновить модель в `models/`
2. Обновить схему в `schemas/`
3. Обновить CRUD операции
4. Запустить миграцию базы данных

### Добавление новых ролей
1. Создать роль через API
2. Назначить пользователям
3. Обновить логику авторизации при необходимости

---

**Модуль готов к использованию в продакшене! 🚀**
