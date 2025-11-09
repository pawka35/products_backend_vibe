# Быстрое решение проблемы с MySQL на удаленном сервере

## Шаг 1: Диагностика

Выполните на сервере:
```bash
cd /path/to/your/project
./diagnose_mysql.sh
```

Или вручную:
```bash
# Проверьте логи
docker-compose logs mysql

# Проверьте статус
docker-compose ps mysql

# Проверьте порт
netstat -tuln | grep 3307
```

## Шаг 2: Быстрое решение (попробуйте по порядку)

### Решение 1: Пересоздать контейнер с очисткой данных

```bash
# Остановите и удалите контейнер
docker-compose stop mysql
docker-compose rm -f mysql

# Удалите volume (данные будут потеряны!)
docker volume rm $(docker volume ls -q | grep mysql)

# Запустите заново
docker-compose up -d mysql

# Проверьте логи
docker-compose logs -f mysql
```

### Решение 2: Использовать исправленную конфигурацию

```bash
# Используйте файл с оптимизированными настройками
docker-compose -f docker-compose.fix-mysql.yml down
docker-compose -f docker-compose.fix-mysql.yml up -d mysql

# Проверьте статус
docker-compose -f docker-compose.fix-mysql.yml ps mysql
```

### Решение 3: Увеличить время на старт

Если MySQL долго инициализируется, временно отключите healthcheck:

Измените `docker-compose.yml`:
```yaml
mysql:
  # ... другие настройки
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
    interval: 30s
    timeout: 10s
    retries: 10
    start_period: 120s  # Увеличьте до 2 минут
```

Затем:
```bash
docker-compose up -d mysql
```

### Решение 4: Проверить ресурсы сервера

```bash
# Проверьте память
free -h

# Проверьте диск
df -h

# Если памяти меньше 512MB, используйте облегченную версию MySQL
docker-compose -f docker-compose.fix-mysql.yml up -d mysql
```

### Решение 5: Использовать MySQL 5.7 (для очень старых серверов)

Создайте `docker-compose.mysql57.yml`:
```yaml
version: '3.8'
services:
  mysql:
    image: mysql:5.7
    # ... остальные настройки такие же
```

Запустите:
```bash
docker-compose -f docker-compose.mysql57.yml up -d mysql
```

## Шаг 3: Проверка

После применения решения проверьте:

```bash
# Статус контейнера
docker-compose ps mysql

# Должно быть: "Up" и "healthy"

# Логи (должны быть без ошибок)
docker-compose logs mysql --tail=50

# Подключение к MySQL
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password -e "SHOW DATABASES;"
```

## Шаг 4: Если ничего не помогло

### Вариант A: Использовать внешний MySQL

Установите MySQL на хосте:
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation

# Создайте базу данных
sudo mysql -e "CREATE DATABASE fastapi_auth;"
sudo mysql -e "CREATE USER 'fastapi_user'@'localhost' IDENTIFIED BY 'fastapi_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON fastapi_auth.* TO 'fastapi_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
```

Измените `docker-compose.yml`:
- Удалите сервис `mysql`
- Измените `DATABASE_URL` в FastAPI на `mysql+pymysql://fastapi_user:fastapi_password@host.docker.internal:3306/fastapi_auth`

### Вариант B: Использовать MariaDB (легче для старых серверов)

Замените MySQL на MariaDB в `docker-compose.yml`:
```yaml
mysql:
  image: mariadb:10.5
  # ... остальные настройки такие же
```

## Частые ошибки и решения

### Ошибка: "Can't create/write to file"
**Решение:** Проблема с правами доступа к volumes
```bash
sudo chown -R 999:999 /var/lib/docker/volumes/
```

### Ошибка: "Port already in use"
**Решение:** Порт 3307 занят, измените порт в `docker-compose.yml`

### Ошибка: "Out of memory"
**Решение:** Недостаточно памяти, используйте `docker-compose.fix-mysql.yml`

### Ошибка: "MySQL server has gone away"
**Решение:** Увеличьте таймауты в MySQL конфигурации

## Получить помощь

Если проблема не решена, соберите информацию:
```bash
# Логи
docker-compose logs mysql > mysql_logs.txt

# Статус
docker-compose ps > status.txt

# Информация о системе
free -h > memory.txt
df -h > disk.txt
docker info > docker_info.txt
```

Отправьте эти файлы для анализа.

