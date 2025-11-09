# Решение проблемы: MariaDB не может инициализироваться

## Проблема

```
[ERROR] Could not open mysql.plugin table: "Table 'mysql.plugin' doesn't exist"
[ERROR] Unknown/unsupported storage engine: InnoDB
[ERROR] Aborting
```

Это означает, что база данных MariaDB не была инициализирована правильно или volume поврежден.

## Быстрое решение

### Вариант 1: Использовать скрипт автоматического исправления

```bash
chmod +x fix_mariadb_init.sh
./fix_mariadb_init.sh
```

Скрипт:
1. Остановит все контейнеры
2. Удалит поврежденный volume
3. Пересоздаст базу данных с нуля
4. Проверит, что все работает

### Вариант 2: Ручное исправление

```bash
# 1. Остановите все контейнеры
docker compose down

# 2. Удалите volume с данными
docker volume ls | grep mysql
docker volume rm $(docker volume ls -q | grep mysql)

# 3. Очистите неиспользуемые volumes
docker volume prune -f

# 4. Запустите заново
docker compose up -d mysql

# 5. Проверьте логи
docker compose logs -f mysql
```

## Причины проблемы

### Причина 1: Поврежденный volume

**Симптомы:**
- Ошибки о несуществующих таблицах
- Ошибки о неподдерживаемых storage engines
- База данных не может запуститься

**Решение:**
Удалите volume и пересоздайте базу данных (см. выше).

### Причина 2: Конфликт версий

**Симптомы:**
- Volume был создан с другой версией MySQL/MariaDB
- Несовместимые форматы данных

**Решение:**
Используйте скрипт `fix_mariadb_init.sh` для полной переустановки.

### Причина 3: Неправильная инициализация

**Симптомы:**
- База данных не инициализировалась при первом запуске
- Volume пустой или содержит неполные данные

**Решение:**
Убедитесь, что volume создается с нуля при первом запуске.

## Пошаговое исправление

### Шаг 1: Остановка контейнеров

```bash
docker compose down
```

### Шаг 2: Удаление volume

```bash
# Найти volume
docker volume ls | grep mysql

# Удалить volume
docker volume rm products_backend_vibe_mysql_data

# Или удалить все volumes с mysql в названии
docker volume rm $(docker volume ls -q | grep mysql)
```

### Шаг 3: Очистка

```bash
# Очистить неиспользуемые volumes
docker volume prune -f

# Очистить неиспользуемые образы (опционально)
docker image prune -a -f
```

### Шаг 4: Перезапуск

```bash
# Запустить только MySQL сначала
docker compose up -d mysql

# Дождаться, пока станет healthy
docker compose ps mysql

# Проверить логи
docker compose logs -f mysql
```

### Шаг 5: Проверка

```bash
# Статус должен быть "Up" и "healthy"
docker compose ps mysql

# Логи не должны содержать ошибок
docker compose logs mysql --tail=50

# Проверка подключения
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password -e "SHOW DATABASES;"
```

## Альтернативные решения

### Решение 1: Использовать более новую версию MariaDB

Если проблема сохраняется, попробуйте использовать MariaDB 10.6:

```yaml
mysql:
  image: mariadb:10.6
  # ... остальные настройки
```

### Решение 2: Использовать MySQL 5.7

Если MariaDB не работает, используйте MySQL 5.7:

```bash
docker compose -f docker-compose.mysql57.yml up -d mysql
```

### Решение 3: Использовать внешний MySQL

Установите MySQL на хосте и используйте его вместо контейнера.

## Предотвращение проблемы

### 1. Регулярные бэкапы

```bash
# Создать бэкап
docker exec fastapi_mysql mysqldump -u fastapi_user -pfastapi_password fastapi_auth > backup.sql

# Восстановить из бэкапа
docker exec -i fastapi_mysql mysql -u fastapi_user -pfastapi_password fastapi_auth < backup.sql
```

### 2. Мониторинг volumes

```bash
# Проверить размер volume
docker system df -v

# Проверить использование места
df -h
```

### 3. Правильное завершение

Всегда используйте `docker compose down` для корректного завершения контейнеров.

## Проверка после исправления

```bash
# 1. Статус контейнера
docker compose ps mysql
# Должно быть "Up" и "healthy"

# 2. Логи (не должно быть ошибок)
docker compose logs mysql --tail=50

# 3. Подключение к базе данных
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password -e "SHOW DATABASES;"

# 4. Проверка таблиц
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password fastapi_auth -e "SHOW TABLES;"
```

## Если проблема сохраняется

1. Проверьте системные ресурсы:
```bash
free -h
df -h
```

2. Проверьте логи Docker:
```bash
journalctl -u docker
```

3. Попробуйте другую версию MariaDB:
```yaml
image: mariadb:10.6
# или
image: mariadb:10.4
```

4. Используйте MySQL 5.7:
```bash
docker compose -f docker-compose.mysql57.yml up -d mysql
```

## Полезные команды

```bash
# Просмотр volumes
docker volume ls
docker volume inspect products_backend_vibe_mysql_data

# Просмотр логов
docker compose logs -f mysql

# Перезапуск контейнера
docker compose restart mysql

# Проверка подключения
docker exec -it fastapi_mysql mysql -u root -prootpassword -e "SELECT VERSION();"
```

## Важные замечания

1. **Удаление volume удалит все данные** - убедитесь, что у вас есть бэкап, если нужны данные
2. **Инициализация может занять время** - подождите 30-60 секунд после запуска
3. **Проверяйте логи** - они покажут, что именно пошло не так
4. **Используйте healthcheck** - он покажет, когда база данных готова

## После исправления

После успешного исправления:

1. Запустите FastAPI:
```bash
docker compose up -d fastapi
```

2. Проверьте, что все работает:
```bash
docker compose ps
```

3. Проверьте доступность:
```bash
curl http://localhost/health
```

