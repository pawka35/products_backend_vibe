# FastAPI Auth System

Система аутентификации на FastAPI с JWT токенами и MySQL базой данных.

## Возможности

- Регистрация и авторизация пользователей
- JWT токены для аутентификации
- Три роли пользователей: admin, customer, executor
- Защищенные эндпоинты с проверкой ролей
- MySQL база данных
- Модульная архитектура с роутерами в отдельных папках

## Установка и запуск

### 1. Запуск MySQL в Docker

```bash
docker-compose up -d
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
DATABASE_URL=mysql+pymysql://fastapi_user:fastapi_password@localhost:3306/fastapi_auth
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Запуск приложения

```bash
python main.py
```

Или с uvicorn:

```bash
uvicorn main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

## API Endpoints

### Публичные эндпоинты

- `GET /` - Главная страница
- `GET /health` - Проверка состояния приложения

### Авторизация (`/auth`)

- `POST /auth/register` - Регистрация нового пользователя
- `POST /auth/token` - Получение JWT токена (авторизация)
- `GET /auth/me` - Информация о текущем пользователе
- `POST /auth/refresh` - Обновление JWT токена

### Управление пользователями (`/users`)

- `GET /users` - Список всех пользователей (только для админов)
- `GET /users/{user_id}` - Информация о конкретном пользователе
- `GET /users/role/{role}` - Пользователи по роли (только для админов)

## Роли пользователей

- **admin** - Полный доступ ко всем эндпоинтам
- **customer** - Доступ только к своим данным
- **executor** - Доступ только к своим данным

## Структура проекта

```
├── main.py              # Основное приложение FastAPI
├── auth/                # Папка для приложения авторизации
│   ├── __init__.py
│   └── router.py        # Роутер для авторизации (/auth)
├── app/                 # Папка для основного приложения
│   ├── __init__.py
│   └── users.py         # Роутер для управления пользователями (/users)
├── models.py            # Модели базы данных
├── schemas.py           # Pydantic схемы
├── auth.py              # Аутентификация и JWT
├── crud.py              # CRUD операции
├── database.py          # Настройка базы данных
├── config.py            # Конфигурация
├── requirements.txt     # Зависимости
└── docker-compose.yml   # Docker для MySQL
```

## Примеры использования

### Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "password123",
       "role": "customer"
     }'
```

### Получение токена

```bash
curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=password123"
```

### Доступ к защищенному эндпоинту

```bash
curl -X GET "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Обновление токена

```bash
curl -X POST "http://localhost:8000/auth/refresh" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Получение списка пользователей (только для админов)

```bash
curl -X GET "http://localhost:8000/users" \
     -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

## Документация API

После запуска приложения документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Архитектура

Проект использует модульную архитектуру с роутерами в отдельных папках:

- **`auth/`** - содержит приложение авторизации с роутером `/auth`
- **`app/`** - содержит основное приложение с роутером `/users`
- **`main.py`** - основное приложение, которое подключает все роутеры

### Преимущества новой структуры:

- **Организация**: логически связанные модули в отдельных папках
- **Масштабируемость**: легко добавлять новые приложения и роутеры
- **Читаемость**: код лучше организован и понятен
- **Переиспользование**: модули можно использовать в других проектах
- **Тестирование**: проще писать тесты для отдельных модулей

### Добавление новых приложений:

Для добавления нового приложения создайте новую папку с `__init__.py` и модулями, затем подключите роутер в `main.py`.
