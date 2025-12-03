# FastAPI Backend System

Полнофункциональная система управления пользователями, ролями, заказами и поиском продуктов, построенная на FastAPI.

## 🚀 Основные возможности

### 🔐 Аутентификация и авторизация
- Регистрация и вход пользователей
- JWT токены для аутентификации
- Ролевая система доступа (RBAC)
- Защита от создания администраторов через регистрацию

### 👥 Управление пользователями
- CRUD операции с пользователями
- Роли: admin, customer, executor
- Административные функции управления пользователями
- Автоматическое создание первого администратора при запуске
- Скрипт для сброса пароля администратора (`reset_admin_password.py`)

### 🎭 Управление ролями
- Создание и управление ролями (только для администраторов)
- Назначение ролей пользователям
- Базовые роли (из таблицы users) + дополнительные роли (из таблицы user_roles)
- Удаление ролей у пользователей

### 📦 Система заказов
- Создание заказов с продуктами
- Исполнение заказов
- Отслеживание статуса заказов
- Управление продуктами в заказах
- Статистика заказов по статусам для customer и executor
- Фильтрация статистики по конкретному статусу

### 🔍 Поиск продуктов
- Поиск по внешнему API (MaxiRetail)
- Пагинация результатов
- Кэширование результатов поиска

## 🏗️ Архитектура

```
backend/
├── app/                    # Основное приложение
│   ├── admin/             # Административные функции
│   ├── crud/              # CRUD операции
│   ├── models/            # Модели данных
│   ├── routers/           # API роутеры
│   └── schemas/           # Pydantic схемы
├── auth/                  # Аутентификация и авторизация
│   ├── crud/              # CRUD для пользователей и ролей
│   ├── models/            # Модели пользователей и ролей
│   ├── routers/           # Роутеры аутентификации
│   ├── schemas/           # Схемы пользователей и ролей
│   ├── tests/             # Тесты аутентификации
│   └── utils/             # Утилиты (инициализация админа)
├── products/              # Управление продуктами и заказами
│   ├── crud/              # CRUD для продуктов и заказов
│   ├── models/            # Модели продуктов и заказов
│   ├── routers/           # Роутеры продуктов и заказов
│   ├── schemas/           # Схемы продуктов и заказов
│   ├── services/          # Сервисы (поиск)
│   └── tests/             # Тесты продуктов
├── config.py              # Конфигурация
├── database.py            # Настройки базы данных
├── main.py                # Главный файл приложения
└── requirements.txt       # Зависимости
```

## 🛠️ Технологии

- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **Pydantic** - валидация данных
- **MySQL** - база данных
- **JWT** - токены аутентификации
- **Docker** - контейнеризация
- **Nginx** - обратный прокси

## 🚀 Быстрый старт

### Локальная разработка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd backend
```

2. **Активация виртуального окружения**
```bash
source venv/bin/activate
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка базы данных**
```bash
# Создайте файл config.env с настройками
cp config.env.example config.env
# Отредактируйте config.env
```

5. **Запуск MySQL**
```bash
./dev.sh
```

6. **Запуск приложения**
```bash
python main.py
```

### Docker

1. **Сборка и запуск**
```bash
docker compose up --build
```

2. **Остановка**
```bash
docker compose down
```

## 📚 API Endpoints

### Основные
- `GET /` - Главная страница
- `GET /health` - Проверка здоровья сервиса
- `GET /api/docs` - Swagger документация
- `GET /api/redoc` - ReDoc документация
- `GET /api/openapi.json` - OpenAPI схема

### Аутентификация
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/token` - Получение JWT токена
- `GET /api/auth/me` - Информация о текущем пользователе
- `PUT /api/auth/me` - Обновление профиля пользователя (username и/или email)
- `PUT /api/auth/me/password` - Изменение пароля текущего пользователя

### Пользователи
- `GET /users/` - Список всех пользователей
- `GET /users/{id}` - Информация о пользователе

### Административные функции (только для администраторов)
- `POST /api/admin/users` - Создание нового пользователя (с любой ролью, включая admin)
- `GET /api/admin/users` - Список всех пользователей с фильтрами и пагинацией
- `GET /api/admin/users/{user_id}` - Детальная информация о пользователе
- `PUT /api/admin/users/{user_id}/role` - Изменение роли пользователя
- `PUT /api/admin/users/{user_id}/password` - Изменение пароля пользователя
- `DELETE /api/admin/users/{user_id}` - Деактивация пользователя
- `GET /api/admin/users/role/{role}` - Пользователи с определенной ролью
- `GET /api/admin/statistics` - Статистика пользователей системы
- `POST /api/admin/users/bulk/change-role` - Массовое изменение ролей пользователей
- `GET /api/admin/orders` - Список всех заказов с фильтрами и пагинацией

### Управление ролями (только для администраторов)
- `GET /api/admin/roles` - Список всех ролей
- `POST /api/admin/roles` - Создание новой роли
- `GET /api/admin/roles/{role_id}` - Получение роли по ID
- `PUT /api/admin/roles/{role_id}` - Обновление роли
- `DELETE /api/admin/roles/{role_id}` - Удаление роли
- `POST /api/admin/roles/{role_id}/activate` - Активация роли
- `GET /api/admin/roles/users/{user_id}` - Роли пользователя
- `GET /api/admin/roles/{role_id}/users` - Пользователи с ролью
- `POST /api/admin/roles/users/assign` - Назначение роли пользователю
- `PUT /api/admin/roles/users/{role_assignment_id}` - Обновление назначения роли пользователю
- `DELETE /api/admin/roles/users/{role_assignment_id}` - Удаление роли у пользователя

### Заказы (Customer)
- `POST /api/customer/orders` - Создание нового заказа
- `GET /api/customer/orders/executors` - Список доступных исполнителей
- `GET /api/customer/orders` - Список заказов текущего пользователя с фильтрами и пагинацией
- `GET /api/customer/orders/{id}` - Детали заказа
- `GET /api/customer/orders/{id}/summary` - Сводка по заказу
- `PUT /api/customer/orders/{id}` - Редактирование заказа (только со статусом pending)
- `POST /api/customer/orders/{id}/copy` - Копирование заказа
- `POST /api/customer/orders/{id}/cancel` - Отмена заказа (только со статусом pending)
- `GET /api/customer/orders/statistics/by-status` - Статистика заказов по статусам (опциональный фильтр `?status=pending`)

### Сохраненные товары (Customer)
- `POST /api/customer/products/saved` - Создание сохраненного товара
- `GET /api/customer/products/saved` - Список сохраненных товаров с пагинацией
- `GET /api/customer/products/saved/{id}` - Детали сохраненного товара
- `PUT /api/customer/products/saved/{id}` - Обновление сохраненного товара
- `DELETE /api/customer/products/saved/{id}` - Удаление сохраненного товара

### Поиск продуктов (Customer)
- `POST /api/customer/search/products` - Поиск продуктов с пагинацией

### Исполнение заказов (Executor)
- `GET /api/executor/orders` - Доступные заказы с фильтрами и пагинацией
- `GET /api/executor/orders/{id}` - Детали заказа
- `GET /api/executor/orders/{id}/summary` - Сводка по заказу
- `PUT /api/executor/orders/{id}/start` - Начало исполнения заказа
- `PUT /api/executor/products/{id}/purchase` - Отметка продукта как купленного
- `PUT /api/executor/products/{id}/unpurchase` - Снятие пометки покупки
- `PUT /api/executor/orders/{id}/complete` - Завершение заказа
- `GET /api/executor/orders/statistics/by-status` - Статистика заказов по статусам (опциональный фильтр `?status=completed`)
- `GET /api/executor/customers` - Список всех заказчиков

### Уведомления (Telegram)
- `POST /api/notifications/telegram/request-code` - Запрос кода верификации для привязки Telegram
- `GET /api/notifications/telegram/status` - Статус подключения Telegram
- `DELETE /api/notifications/telegram/disconnect` - Отвязка Telegram от аккаунта
- `GET /api/notifications/settings` - Получение настроек уведомлений
- `PUT /api/notifications/settings` - Обновление настроек уведомлений
- `POST /api/notifications/telegram/webhook` - Webhook для обработки команд от Telegram бота

## 🔒 Безопасность

- **JWT токены** для аутентификации
- **Ролевая система** для авторизации
- **Хеширование паролей** с bcrypt
- **Защита от создания администраторов** через регистрацию
- **Автоматическая инициализация** первого администратора

### Управление паролем администратора

При первом запуске приложения создается администратор с учетными данными:
- **Username**: `admin`
- **Email**: `admin@system.local`
- **Password**: генерируется случайно и выводится в консоль

**Важно**: Пароль показывается только один раз при создании!

Для сброса пароля администратора используйте скрипт:
```bash
# С случайным паролем
python3 reset_admin_password.py

# С указанным паролем
python3 reset_admin_password.py "новый_пароль"
```

## 🧪 Тестирование

### Запуск всех тестов
```bash
python run_tests.py
```

### Запуск отдельных тестов
```bash
# Тесты аутентификации
python auth/tests/test_auth.py

# Тесты ролей
python auth/tests/test_roles.py

# Тесты административных функций
python auth/tests/test_admin_init.py

# Тесты поиска
cd products && python -m pytest tests/test_search.py -v

# Тесты заказов
python products/tests/test_orders.py
```

## 📊 База данных

### Основные таблицы
- `users` - пользователи системы
- `roles` - роли в системе
- `user_roles` - назначения ролей пользователям
- `orders` - заказы
- `order_products` - продукты в заказах

### Схема ролей
- **admin** - полный доступ к системе
- **customer** - создание и управление заказами
- **executor** - исполнение заказов
- **moderator** - дополнительная роль (пример)

## 🐳 Docker

### Структура Docker
- `fastapi` - основное приложение
- `nginx` - обратный прокси
- `mysql` - база данных

### Переменные окружения
```bash
# config.env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=fastapi_auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📝 Логирование

Система ведет логи всех операций:
- Аутентификация и авторизация
- CRUD операции
- Ошибки и исключения
- HTTP запросы

## 🤝 Разработка

### Структура проекта
- Модульная архитектура
- Разделение на слои (models, schemas, crud, routers)
- Единообразное именование
- Документированные API endpoints

### Стандарты кода
- PEP 8
- Type hints
- Docstrings
- Логирование

## 📈 Мониторинг

- Health check endpoint
- Логирование всех операций
- Обработка ошибок
- Валидация входных данных

## 🔧 Устранение неполадок

### Частые проблемы
1. **Ошибки подключения к БД** - проверьте config.env
2. **Ошибки JWT** - проверьте JWT_SECRET_KEY
3. **Проблемы с правами** - убедитесь, что пользователь имеет нужную роль

### Логи
- Проверьте логи приложения
- Проверьте логи Docker контейнеров
- Используйте health check endpoint

## 📄 Лицензия

MIT License

## 👥 Авторы

Разработано для системы управления заказами и пользователями.

---

**Система готова к продакшену! 🚀**
