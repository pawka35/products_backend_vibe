# Решение проблем с MySQL контейнером на удаленном сервере

## Частые проблемы и решения

### Проблема 1: Контейнер не запускается

**Симптомы:**
- Контейнер постоянно перезапускается
- Статус "Error" или "Restarting"
- Логи показывают ошибки при инициализации

**Решения:**

#### Решение 1.1: Недостаточно памяти

Проверьте доступную память:
```bash
free -h
```

Если памяти меньше 512MB, используйте облегченную конфигурацию:
```bash
docker-compose -f docker-compose.fix-mysql.yml up -d mysql
```

#### Решение 1.2: Проблемы с volumes

Очистите volumes и пересоздайте:
```bash
# Остановите контейнер
docker-compose stop mysql
docker-compose rm -f mysql

# Удалите volume (данные будут потеряны!)
docker volume rm backend_mysql_data

# Запустите заново
docker-compose up -d mysql
```

#### Решение 1.3: Конфликт портов

Проверьте, не занят ли порт 3307:
```bash
netstat -tuln | grep 3307
# или
ss -tuln | grep 3307
```

Если порт занят, измените порт в `docker-compose.yml`:
```yaml
ports:
  - "3308:3306"  # Измените 3307 на другой порт
```

#### Решение 1.4: Проблемы с правами доступа

Создайте директорию для данных и установите права:
```bash
sudo mkdir -p /var/lib/docker/volumes/backend_mysql_data
sudo chown -R 999:999 /var/lib/docker/volumes/backend_mysql_data
```

### Проблема 2: Медленный запуск MySQL

**Симптомы:**
- MySQL долго инициализируется
- Healthcheck не проходит
- Таймауты при подключении

**Решения:**

Используйте исправленную конфигурацию:
```bash
docker-compose -f docker-compose.fix-mysql.yml up -d mysql
```

Эта конфигурация:
- Увеличивает время на старт (start_period: 40s)
- Уменьшает размер буферного пула для старых серверов
- Настраивает оптимальные параметры MySQL

### Проблема 3: Ошибки аутентификации

**Симптомы:**
- Ошибка "Access denied for user"
- Проблемы с подключением из приложения

**Решения:**

Проверьте переменные окружения в `docker-compose.yml`:
```yaml
environment:
  MYSQL_ROOT_PASSWORD: rootpassword
  MYSQL_DATABASE: fastapi_auth
  MYSQL_USER: fastapi_user
  MYSQL_PASSWORD: fastapi_password
```

Убедитесь, что в приложении используется правильный `DATABASE_URL`:
```
DATABASE_URL=mysql+pymysql://fastapi_user:fastapi_password@mysql:3306/fastapi_auth
```

### Проблема 4: Контейнер падает после запуска

**Симптомы:**
- Контейнер запускается, но сразу падает
- В логах ошибки типа "Can't create/write to file"

**Решения:**

#### Решение 4.1: Проблемы с диском

Проверьте свободное место:
```bash
df -h
```

Очистите место, если нужно:
```bash
# Удалите неиспользуемые образы
docker system prune -a

# Удалите неиспользуемые volumes
docker volume prune
```

#### Решение 4.2: Проблемы с SELinux (если используется)

Отключите SELinux или настройте контекст:
```bash
# Временно отключить (только для тестирования!)
sudo setenforce 0

# Или настроить контекст для Docker volumes
sudo chcon -Rt svirt_sandbox_file_t /var/lib/docker/volumes/
```

### Проблема 5: MySQL не доступен из приложения

**Симптомы:**
- FastAPI контейнер не может подключиться к MySQL
- Ошибки "Can't connect to MySQL server"

**Решения:**

#### Решение 5.1: Проверьте сеть Docker

Убедитесь, что контейнеры в одной сети:
```bash
docker network ls
docker network inspect backend_app_network
```

#### Решение 5.2: Проверьте healthcheck

Дождитесь, пока MySQL станет healthy:
```bash
docker-compose ps mysql
# Должно быть "healthy"
```

#### Решение 5.3: Проверьте подключение вручную

Подключитесь к MySQL из контейнера FastAPI:
```bash
docker exec -it fastapi_app bash
# Затем внутри контейнера:
mysql -h mysql -u fastapi_user -pfastapi_password fastapi_auth
```

## Диагностика

Используйте скрипт диагностики:
```bash
chmod +x diagnose_mysql.sh
./diagnose_mysql.sh
```

## Быстрое решение

Если ничего не помогло, выполните полную переустановку:

```bash
# 1. Остановите все контейнеры
docker-compose down

# 2. Удалите volumes
docker volume rm backend_mysql_data

# 3. Используйте исправленную конфигурацию
docker-compose -f docker-compose.fix-mysql.yml up -d mysql

# 4. Проверьте логи
docker-compose -f docker-compose.fix-mysql.yml logs -f mysql
```

## Альтернатива: Использование внешнего MySQL

Если проблемы с Docker MySQL продолжаются, используйте внешний MySQL сервер:

1. Установите MySQL на хосте:
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

2. Создайте базу данных:
```sql
CREATE DATABASE fastapi_auth;
CREATE USER 'fastapi_user'@'localhost' IDENTIFIED BY 'fastapi_password';
GRANT ALL PRIVILEGES ON fastapi_auth.* TO 'fastapi_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Измените `docker-compose.yml`:
```yaml
fastapi:
  environment:
    - DATABASE_URL=mysql+pymysql://fastapi_user:fastapi_password@host.docker.internal:3306/fastapi_auth
  # Уберите depends_on: mysql
```

4. Удалите сервис MySQL из `docker-compose.yml`

## Проверка после исправления

```bash
# Проверьте статус
docker-compose ps

# Проверьте логи
docker-compose logs mysql

# Проверьте подключение
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password -e "SHOW DATABASES;"
```

## Получение логов для диагностики

Сохраните логи для анализа:
```bash
docker-compose logs mysql > mysql_logs.txt
docker-compose ps > containers_status.txt
docker info > docker_info.txt
```

Отправьте эти файлы для дальнейшей диагностики.

