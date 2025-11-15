# Инструкция по деплою изменений на продакшен

## Быстрый деплой

### Вариант 1: Использование скрипта (рекомендуется)

```bash
# На сервере
cd /path/to/backend
./deploy.sh
```

Скрипт автоматически:
1. Обновит код из репозитория
2. Выполнит миграции (если нужно)
3. Пересоберет контейнеры
4. Перезапустит сервисы
5. Покажет статус

### Вариант 2: Ручной деплой

#### 1. Подключитесь к серверу

```bash
ssh user@195.234.208.160
# или
ssh user@products.bunkov.in
```

#### 2. Перейдите в директорию проекта

```bash
cd /path/to/backend  # замените на путь к вашему проекту
```

#### 3. Обновите код из репозитория

```bash
# Убедитесь, что вы на ветке main
git checkout main

# Получите последние изменения
git pull origin main
```

#### 4. Выполните миграции базы данных (если есть новые)

```bash
# Вариант 1: Внутри контейнера (рекомендуется)
docker compose exec fastapi python3 migrations/add_telegram_notifications.py

# Вариант 2: Локально (если есть виртуальное окружение)
source venv/bin/activate
python3 migrations/add_telegram_notifications.py
```

#### 5. Пересоберите контейнеры

```bash
# Пересборка всех контейнеров
docker compose build

# Или пересборка только FastAPI (если изменился только код приложения)
docker compose build fastapi
```

#### 6. Перезапустите сервисы

```bash
# Перезапуск всех сервисов
docker compose up -d

# Или перезапуск только FastAPI
docker compose restart fastapi
```

#### 7. Проверьте статус

```bash
# Проверка статуса контейнеров
docker compose ps

# Проверка логов
docker compose logs --tail=50 fastapi

# Проверка health check
curl https://products.bunkov.in/health
```

## Что происходит при деплое

### При изменении кода приложения (Python)

1. **Обновление кода** - `git pull` получает новые изменения
2. **Пересборка контейнера** - `docker compose build` пересобирает образ с новым кодом
3. **Перезапуск** - `docker compose up -d` запускает новый контейнер
4. **Миграции** - выполняются автоматически при старте приложения (если настроено) или вручную

### При изменении конфигурации (nginx, docker-compose.yml)

1. **Обновление кода** - `git pull`
2. **Пересборка** - `docker compose build nginx` (если изменился Dockerfile)
3. **Перезапуск** - `docker compose restart nginx` или `docker compose up -d nginx`

### При изменении зависимостей (requirements.txt)

1. **Обновление кода** - `git pull`
2. **Пересборка** - `docker compose build fastapi` (обязательно, т.к. зависимости устанавливаются при сборке)
3. **Перезапуск** - `docker compose up -d fastapi`

## Проверка после деплоя

### 1. Проверка контейнеров

```bash
docker compose ps
```

Все контейнеры должны быть в статусе `Up` или `Up (healthy)`.

### 2. Проверка логов

```bash
# Логи FastAPI
docker compose logs --tail=50 fastapi

# Логи Nginx
docker compose logs --tail=50 nginx

# Логи MySQL
docker compose logs --tail=50 mysql
```

### 3. Проверка работы API

```bash
# Health check
curl https://products.bunkov.in/health

# Проверка документации
curl -I https://products.bunkov.in/docs
```

### 4. Проверка базы данных

```bash
# Подключение к БД через контейнер
docker compose exec mysql mysql -u fastapi_user -pfastapi_password fastapi_auth

# Проверка таблиц
SHOW TABLES;
```

## Откат изменений (rollback)

Если что-то пошло не так:

```bash
# 1. Вернуться к предыдущему коммиту
git checkout <previous-commit-hash>

# 2. Пересобрать и перезапустить
docker compose build fastapi
docker compose up -d fastapi
```

Или использовать git:

```bash
# Откатить последний коммит
git reset --hard HEAD~1

# Пересобрать и перезапустить
docker compose build fastapi
docker compose up -d fastapi
```

## Частые проблемы

### Контейнер не запускается

```bash
# Проверьте логи
docker compose logs fastapi

# Проверьте конфигурацию
docker compose config
```

### Ошибки при миграции

```bash
# Выполните миграцию вручную
docker compose exec fastapi python3 migrations/add_telegram_notifications.py

# Или локально
source venv/bin/activate
python3 migrations/add_telegram_notifications.py
```

### Порты заняты

```bash
# Проверьте, какие процессы используют порты
sudo netstat -tulpn | grep -E ':(80|443|8000|3307)'

# Остановите конфликтующие сервисы
sudo systemctl stop apache2  # если установлен
sudo systemctl stop nginx    # если установлен системный
```

### Изменения не применяются

```bash
# Убедитесь, что код обновлен
git status
git log --oneline -5

# Принудительно пересоберите без кеша
docker compose build --no-cache fastapi
docker compose up -d fastapi
```

## Автоматизация деплоя (опционально)

Можно настроить автоматический деплой через GitHub Actions или GitLab CI/CD:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          ssh user@server 'cd /path/to/backend && ./deploy.sh'
```

## Безопасность

- ✅ Всегда проверяйте изменения перед деплоем
- ✅ Используйте тестовую среду для проверки
- ✅ Делайте бэкап базы данных перед миграциями
- ✅ Проверяйте логи после деплоя
- ✅ Имейте план отката (rollback)

