# Локальная разработка (без Docker)

Инструкция по запуску приложения локально для разработки.

## Быстрый старт

### 1. Активируйте виртуальное окружение

```bash
source venv/bin/activate
```

Если виртуального окружения нет, создайте его:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте переменные окружения

Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

Отредактируйте `.env` и укажите настройки:

```env
# База данных (для локальной разработки)
DATABASE_URL=mysql+pymysql://fastapi_user:fastapi_password@localhost:3307/fastapi_auth

# Секретный ключ (можно оставить по умолчанию для разработки)
SECRET_KEY=your-secret-key-here-change-in-production

# Telegram (опционально, для тестирования уведомлений)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ENABLED=true
```

### 4. Настройте базу данных

#### Вариант 1: Использовать Docker только для БД

```bash
# Запустите только MySQL контейнер
docker compose up -d mysql

# Дождитесь, пока БД будет готова
docker compose ps mysql
```

#### Вариант 2: Локальная MySQL/MariaDB

Установите MySQL или MariaDB локально:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# Или MariaDB
sudo apt install mariadb-server
```

Создайте базу данных и пользователя:

```sql
CREATE DATABASE fastapi_auth CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'fastapi_user'@'localhost' IDENTIFIED BY 'fastapi_password';
GRANT ALL PRIVILEGES ON fastapi_auth.* TO 'fastapi_user'@'localhost';
FLUSH PRIVILEGES;
```

Обновите `DATABASE_URL` в `.env`:

```env
DATABASE_URL=mysql+pymysql://fastapi_user:fastapi_password@localhost:3306/fastapi_auth
```

### 5. Выполните миграции

```bash
# Миграция для Telegram уведомлений
python3 migrations/add_telegram_notifications.py
```

### 6. Запустите приложение

#### Вариант 1: Использовать скрипт (рекомендуется)

```bash
./run_local.sh
```

#### Вариант 2: Запустить вручную

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите приложение
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Флаг `--reload` включает автоматическую перезагрузку при изменении кода.

### 7. Проверьте работу

- API: http://localhost:8000
- Документация: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Структура для разработки

```
backend/
├── venv/              # Виртуальное окружение (не коммитится)
├── .env               # Переменные окружения (не коммитится)
├── main.py            # Точка входа приложения
├── requirements.txt   # Зависимости Python
├── run_local.sh       # Скрипт для локального запуска
└── ...
```

## Полезные команды

### Активировать виртуальное окружение

```bash
source venv/bin/activate
```

### Деактивировать виртуальное окружение

```bash
deactivate
```

### Установить новые зависимости

```bash
pip install package_name
pip freeze > requirements.txt  # Обновить requirements.txt
```

### Выполнить миграции

```bash
python3 migrations/add_telegram_notifications.py
```

### Запустить с отладкой

```bash
# С включенным логированием
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Проверить подключение к БД

```bash
python3 -c "from database import wait_for_database; wait_for_database()"
```

## Настройка IDE

### VS Code

Создайте `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true
}
```

### PyCharm

1. File → Settings → Project → Python Interpreter
2. Выберите виртуальное окружение: `venv/bin/python`

## Отладка

### Проблемы с подключением к БД

```bash
# Проверьте, запущен ли MySQL
docker compose ps mysql
# или
sudo systemctl status mysql

# Проверьте подключение
mysql -u fastapi_user -pfastapi_password -h localhost -P 3307 fastapi_auth
```

### Проблемы с зависимостями

```bash
# Переустановите зависимости
pip install --upgrade -r requirements.txt
```

### Проблемы с миграциями

```bash
# Выполните миграцию вручную
python3 migrations/add_telegram_notifications.py
```

## Разработка с Docker (альтернатива)

Если хотите использовать Docker для разработки:

```bash
# Запустить все сервисы
docker compose up -d

# Просмотр логов
docker compose logs -f fastapi

# Выполнить команду в контейнере
docker compose exec fastapi python3 migrations/add_telegram_notifications.py

# Перезапустить после изменений
docker compose restart fastapi
```

## Переменные окружения для разработки

Минимальный `.env` для локальной разработки:

```env
# База данных
DATABASE_URL=mysql+pymysql://fastapi_user:fastapi_password@localhost:3307/fastapi_auth

# Секретный ключ (для разработки можно использовать любой)
SECRET_KEY=dev-secret-key-change-in-production

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=
TELEGRAM_ENABLED=false
```

## Горячая перезагрузка

При использовании `--reload` uvicorn автоматически перезагружает приложение при изменении:
- Python файлов (`.py`)
- Конфигурационных файлов

Изменения применяются автоматически, перезапуск не требуется.

## Тестирование API

### Использование curl

```bash
# Health check
curl http://localhost:8000/health

# Регистрация пользователя
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"test123456","role":"customer"}'
```

### Использование Swagger UI

Откройте http://localhost:8000/docs в браузере для интерактивной документации API.

## Полезные ссылки

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [Uvicorn документация](https://www.uvicorn.org/)
- [SQLAlchemy документация](https://docs.sqlalchemy.org/)

