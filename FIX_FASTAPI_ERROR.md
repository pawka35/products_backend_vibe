# Решение проблемы: Container fastapi_app Error

## Проблема

Контейнер `fastapi_app` не запускается и выдает ошибку при старте.

## Быстрое решение

### Шаг 1: Просмотр логов

```bash
# Просмотр полных логов FastAPI
docker compose logs fastapi

# Или в реальном времени
docker compose logs -f fastapi
```

### Шаг 2: Проверка ошибок

Используйте скрипт диагностики:
```bash
chmod +x check_fastapi_error.sh
./check_fastapi_error.sh
```

### Шаг 3: Перезапуск с просмотром ошибок

```bash
# Остановите контейнер
docker compose stop fastapi

# Запустите в foreground для просмотра ошибок
docker compose up fastapi
```

## Частые причины и решения

### Причина 1: Ошибки подключения к базе данных

**Симптомы:**
- Ошибки типа "Can't connect to MySQL server"
- "Access denied for user"
- "Unknown database"

**Решение:**

1. Убедитесь, что MySQL/MariaDB запущен и healthy:
```bash
docker compose ps mysql
# Должно быть "Up" и "healthy"
```

2. Проверьте переменную DATABASE_URL:
```bash
docker compose config | grep DATABASE_URL
```

3. Проверьте подключение из контейнера FastAPI:
```bash
docker exec fastapi_app python -c "from database import engine; engine.connect()"
```

### Причина 2: Ошибки инициализации базы данных

**Симптомы:**
- Ошибки при создании таблиц
- Ошибки при инициализации ролей
- Ошибки при создании администратора

**Решение:**

Обновленный код теперь обрабатывает эти ошибки и не прерывает запуск приложения. Но если проблема сохраняется:

1. Проверьте логи:
```bash
docker compose logs fastapi | grep -i error
```

2. Проверьте подключение к БД вручную:
```bash
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password fastapi_auth -e "SHOW TABLES;"
```

### Причина 3: Ошибки импорта модулей

**Симптомы:**
- "ModuleNotFoundError"
- "ImportError"
- "No module named"

**Решение:**

1. Проверьте, что все зависимости установлены:
```bash
docker compose exec fastapi pip list
```

2. Пересоберите образ:
```bash
docker compose build --no-cache fastapi
docker compose up -d fastapi
```

### Причина 4: Ошибки в коде приложения

**Симптомы:**
- SyntaxError
- IndentationError
- AttributeError

**Решение:**

1. Проверьте логи на наличие ошибок Python:
```bash
docker compose logs fastapi | grep -i "error\|exception\|traceback"
```

2. Проверьте синтаксис локально:
```bash
python -m py_compile main.py
```

### Причина 5: Недостаточно ресурсов

**Симптомы:**
- Контейнер запускается и сразу падает
- Ошибки памяти

**Решение:**

1. Проверьте ресурсы:
```bash
free -h
df -h
```

2. Увеличьте лимиты в docker-compose.yml (если нужно)

### Причина 6: Проблемы с правами доступа

**Симптомы:**
- "Permission denied"
- Ошибки при записи в файлы

**Решение:**

1. Проверьте права на директорию logs:
```bash
ls -la logs/
```

2. Создайте директорию, если её нет:
```bash
mkdir -p logs
chmod 777 logs
```

## Пошаговое исправление

### Вариант 1: Полная переустановка

```bash
# 1. Остановите все контейнеры
docker compose down

# 2. Пересоберите образ FastAPI
docker compose build --no-cache fastapi

# 3. Запустите MySQL сначала
docker compose up -d mysql

# 4. Дождитесь, пока MySQL станет healthy
docker compose ps mysql
# Должно быть "healthy"

# 5. Запустите FastAPI
docker compose up -d fastapi

# 6. Проверьте логи
docker compose logs -f fastapi
```

### Вариант 2: Постепенное исправление

```bash
# 1. Остановите FastAPI
docker compose stop fastapi

# 2. Удалите контейнер
docker compose rm -f fastapi

# 3. Проверьте MySQL
docker compose ps mysql
# Должно быть "healthy"

# 4. Запустите FastAPI в foreground для просмотра ошибок
docker compose up fastapi
```

## Проверка после исправления

```bash
# 1. Проверьте статус
docker compose ps fastapi
# Должно быть "Up" и через время "healthy"

# 2. Проверьте логи
docker compose logs fastapi --tail=50
# Не должно быть ошибок

# 3. Проверьте healthcheck
curl http://localhost:8000/health
# Должен вернуть JSON

# 4. Проверьте доступность через Nginx
curl http://localhost/health
```

## Дополнительная диагностика

### Проверка внутри контейнера

```bash
# Войдите в контейнер
docker compose exec fastapi bash

# Проверьте Python
python --version

# Проверьте подключение к БД
python -c "from database import engine; print(engine.url)"

# Попробуйте запустить приложение вручную
python main.py
```

### Проверка переменных окружения

```bash
# Просмотр всех переменных
docker compose exec fastapi env

# Проверка конкретной переменной
docker compose exec fastapi env | grep DATABASE_URL
```

### Проверка файлов в контейнере

```bash
# Список файлов
docker compose exec fastapi ls -la

# Проверка main.py
docker compose exec fastapi cat main.py | head -20
```

## Если ничего не помогло

1. Соберите информацию:
```bash
# Логи
docker compose logs fastapi > fastapi_logs.txt

# Конфигурация
docker compose config > docker_compose_config.txt

# Статус контейнеров
docker compose ps > containers_status.txt
```

2. Проверьте системные логи:
```bash
journalctl -u docker
```

3. Попробуйте запустить приложение локально (без Docker):
```bash
# Установите зависимости
pip install -r requirements.txt

# Настройте .env файл
cp env.example .env
# Отредактируйте .env

# Запустите приложение
python main.py
```

Если локально работает, проблема в Docker конфигурации.

## Полезные команды

```bash
# Просмотр логов в реальном времени
docker compose logs -f fastapi

# Перезапуск контейнера
docker compose restart fastapi

# Пересборка образа
docker compose build fastapi
docker compose up -d fastapi

# Очистка неиспользуемых образов
docker system prune -a

# Просмотр использования ресурсов
docker stats
```

## Обновления в коде

В последней версии добавлено:

1. **Обработка ошибок при инициализации БД:**
   - Приложение не падает при ошибках инициализации
   - Детальное логирование ошибок
   - Продолжение работы даже при проблемах с БД

2. **Улучшенное логирование:**
   - Подробные сообщения о каждом шаге инициализации
   - Вывод ошибок с traceback
   - Информация о статусе операций

3. **Увеличенные таймауты:**
   - start_period увеличен до 90 секунд
   - Больше попыток для healthcheck
   - PYTHONUNBUFFERED=1 для немедленного вывода логов

После обновления кода выполните:
```bash
git pull
docker compose build --no-cache fastapi
docker compose up -d fastapi
docker compose logs -f fastapi
```

