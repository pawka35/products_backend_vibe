# Решение проблемы 502 Bad Gateway

## Проблема

При обращении к серверу по IP получается ошибка `502 Bad Gateway`.

Это означает, что Nginx не может подключиться к FastAPI приложению.

## Быстрое решение

### Шаг 1: Диагностика

Выполните на сервере:
```bash
./diagnose_502.sh
```

Или вручную проверьте:
```bash
# Статус контейнеров
docker compose ps

# Логи FastAPI
docker compose logs fastapi --tail=50

# Логи Nginx
docker compose logs nginx --tail=50
```

### Шаг 2: Проверьте, что FastAPI запущен и слушает

```bash
# Проверка внутри контейнера FastAPI
docker exec fastapi_app netstat -tuln | grep 8000

# Или проверка через curl
docker exec fastapi_app curl http://localhost:8000/health
```

### Шаг 3: Проверьте подключение из Nginx к FastAPI

```bash
# Проверка из контейнера Nginx
docker exec fastapi_nginx curl http://fastapi:8000/health
```

Если эта команда не работает, проблема в сети Docker.

### Шаг 4: Перезапустите контейнеры

```bash
# Остановите все контейнеры
docker compose down

# Запустите заново
docker compose up -d

# Проверьте логи
docker compose logs -f
```

## Частые причины и решения

### Причина 1: FastAPI не запускается

**Симптомы:**
- В логах FastAPI есть ошибки
- Контейнер постоянно перезапускается
- Порт 8000 не слушается

**Решение:**

1. Проверьте логи:
```bash
docker compose logs fastapi
```

2. Частые проблемы:
   - Ошибки подключения к БД
   - Ошибки импорта модулей
   - Проблемы с переменными окружения

3. Проверьте подключение к БД:
```bash
# Убедитесь, что MySQL/MariaDB запущен
docker compose ps mysql

# Проверьте переменную DATABASE_URL
docker exec fastapi_app env | grep DATABASE_URL
```

### Причина 2: FastAPI слушает только на localhost

**Симптомы:**
- FastAPI работает локально в контейнере
- Но недоступен из других контейнеров

**Решение:**

Убедитесь, что в `main.py` используется:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

Это уже настроено в проекте, но проверьте, что это действительно используется.

### Причина 3: Проблемы с сетью Docker

**Симптомы:**
- Контейнеры не могут подключиться друг к другу
- DNS не разрешает имена контейнеров

**Решение:**

1. Проверьте сеть:
```bash
docker network inspect backend_app_network
```

2. Убедитесь, что все контейнеры в одной сети:
```bash
docker compose ps
# Все контейнеры должны быть в сети app_network
```

3. Пересоздайте сеть:
```bash
docker compose down
docker network prune -f
docker compose up -d
```

### Причина 4: Nginx не может найти контейнер fastapi

**Симптомы:**
- В логах Nginx ошибки "upstream not found"
- Nginx не может разрешить имя "fastapi"

**Решение:**

1. Убедитесь, что в `nginx.conf` используется правильное имя:
```nginx
upstream fastapi_app {
    server fastapi:8000;
}
```

Имя `fastapi` должно совпадать с именем сервиса в `docker-compose.yml`.

2. Перезапустите Nginx:
```bash
docker compose restart nginx
```

### Причина 5: FastAPI падает при инициализации

**Симптомы:**
- Контейнер запускается и сразу падает
- В логах ошибки при инициализации БД или ролей

**Решение:**

1. Проверьте логи:
```bash
docker compose logs fastapi
```

2. Убедитесь, что БД запущена и доступна:
```bash
# Проверьте статус MySQL/MariaDB
docker compose ps mysql

# Дождитесь, пока БД станет healthy
docker compose ps mysql
# Должно быть "healthy"
```

3. Если БД еще не готова, увеличьте время ожидания:
```yaml
depends_on:
  mysql:
    condition: service_healthy
```

### Причина 6: Проблемы с healthcheck

**Симптомы:**
- FastAPI работает, но healthcheck не проходит
- Nginx не запускается, ожидая FastAPI

**Решение:**

1. Проверьте healthcheck:
```bash
docker exec fastapi_app python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

2. Если healthcheck не работает, временно отключите его:
```yaml
depends_on:
  fastapi:
    condition: service_started
```

## Пошаговое исправление

### Вариант 1: Полная переустановка

```bash
# 1. Остановите все контейнеры
docker compose down

# 2. Удалите volumes (если нужно)
docker volume prune -f

# 3. Пересоберите образы
docker compose build --no-cache

# 4. Запустите заново
docker compose up -d

# 5. Проверьте логи
docker compose logs -f
```

### Вариант 2: Постепенное исправление

```bash
# 1. Проверьте статус MySQL
docker compose ps mysql
# Должно быть "healthy"

# 2. Если MySQL не healthy, исправьте его:
./fix_mysql.sh

# 3. Перезапустите FastAPI
docker compose restart fastapi

# 4. Дождитесь, пока FastAPI станет healthy
docker compose ps fastapi

# 5. Перезапустите Nginx
docker compose restart nginx

# 6. Проверьте логи
docker compose logs -f nginx fastapi
```

## Проверка после исправления

```bash
# 1. Проверьте статус всех контейнеров
docker compose ps
# Все должны быть "Up" и "healthy" (где применимо)

# 2. Проверьте доступность через curl
curl http://localhost/health
# Должен вернуть JSON с информацией о здоровье

# 3. Проверьте доступность через IP сервера
curl http://YOUR_SERVER_IP/health

# 4. Проверьте логи
docker compose logs nginx --tail=20
docker compose logs fastapi --tail=20
```

## Дополнительная диагностика

### Проверка портов

```bash
# На хосте
netstat -tuln | grep -E ":80|:8000"

# В контейнере FastAPI
docker exec fastapi_app netstat -tuln

# В контейнере Nginx
docker exec fastapi_nginx netstat -tuln
```

### Проверка DNS

```bash
# Из контейнера Nginx
docker exec fastapi_nginx nslookup fastapi
docker exec fastapi_nginx getent hosts fastapi
```

### Проверка подключения

```bash
# Из контейнера Nginx к FastAPI
docker exec fastapi_nginx wget -O- http://fastapi:8000/health

# Или через curl
docker exec fastapi_nginx curl http://fastapi:8000/health
```

## Полезные команды

```bash
# Просмотр логов в реальном времени
docker compose logs -f

# Просмотр логов конкретного сервиса
docker compose logs -f fastapi
docker compose logs -f nginx

# Перезапуск сервиса
docker compose restart fastapi
docker compose restart nginx

# Пересборка образа
docker compose build fastapi
docker compose up -d fastapi

# Проверка конфигурации Nginx
docker exec fastapi_nginx nginx -t
```

## Если ничего не помогло

1. Соберите информацию:
```bash
# Логи
docker compose logs > all_logs.txt

# Статус контейнеров
docker compose ps > containers_status.txt

# Конфигурация сети
docker network inspect backend_app_network > network_info.txt
```

2. Проверьте системные ресурсы:
```bash
free -h
df -h
docker system df
```

3. Попробуйте запустить FastAPI без Nginx:
```bash
# Остановите Nginx
docker compose stop nginx

# Обратитесь напрямую к FastAPI
curl http://YOUR_SERVER_IP:8000/health
```

Если это работает, проблема в Nginx конфигурации.

