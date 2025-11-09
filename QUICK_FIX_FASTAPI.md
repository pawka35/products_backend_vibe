# Быстрое решение: Container fastapi_app Error

## Проблема

Контейнер `fastapi_app` не запускается и выдает ошибку.

## Быстрое решение

### Шаг 1: Просмотр логов

```bash
# Быстрая проверка логов
./check_fastapi_logs.sh

# Или вручную
docker compose logs fastapi --tail=100
```

### Шаг 2: Пересборка и перезапуск

```bash
# Обновите код
git pull

# Остановите контейнеры
docker compose down

# Пересоберите образ FastAPI
docker compose build --no-cache fastapi

# Запустите заново
docker compose up -d

# Просмотрите логи в реальном времени
docker compose logs -f fastapi
```

### Шаг 3: Проверка MySQL

Убедитесь, что MySQL запущен и healthy:

```bash
# Проверьте статус
docker compose ps mysql

# Должно быть "Up" и "healthy"

# Если не healthy, исправьте:
./fix_mariadb_init.sh
```

## Что изменилось

### Улучшения в коде:

1. **Ожидание готовности БД:**
   - Приложение теперь ждет до 60 секунд, пока БД станет доступна
   - До 30 попыток подключения с задержкой 2 секунды

2. **Улучшенная обработка ошибок:**
   - Приложение не падает при ошибках инициализации БД
   - Детальное логирование всех шагов
   - Приложение продолжает работу даже при проблемах с БД

3. **Улучшенный healthcheck:**
   - Healthcheck работает даже при проблемах с БД
   - Увеличено время ожидания до 120 секунд
   - Больше попыток для healthcheck

## Частые проблемы

### Проблема 1: БД не готова

**Решение:**
```bash
# Убедитесь, что MySQL healthy
docker compose ps mysql

# Если нет, исправьте:
./fix_mariadb_init.sh
```

### Проблема 2: Ошибки в логах

**Решение:**
```bash
# Просмотрите логи
docker compose logs fastapi

# Найдите ошибки
docker compose logs fastapi | grep -i error
```

### Проблема 3: Проблемы с импортами

**Решение:**
```bash
# Пересоберите образ
docker compose build --no-cache fastapi
```

## Проверка после исправления

```bash
# 1. Статус контейнера
docker compose ps fastapi
# Должно быть "Up" и через время "healthy"

# 2. Логи (не должно быть критических ошибок)
docker compose logs fastapi --tail=50

# 3. Healthcheck
curl http://localhost:8000/health

# 4. Доступность через Nginx
curl http://localhost/health
```

## Если проблема сохраняется

1. Просмотрите полные логи:
```bash
docker compose logs fastapi > fastapi_logs.txt
```

2. Попробуйте запустить в foreground:
```bash
docker compose stop fastapi
docker compose up fastapi
```

3. Проверьте подключение к БД:
```bash
docker exec fastapi_app python -c "from database import engine; engine.connect()"
```

## Дополнительная информация

- Подробное руководство: `FIX_FASTAPI_ERROR.md`
- Скрипт диагностики: `./check_fastapi_logs.sh`
- Скрипт исправления MySQL: `./fix_mariadb_init.sh`

