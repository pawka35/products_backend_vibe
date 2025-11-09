# Быстрое решение: MySQL CPU x86-64-v2 ошибка

## Проблема

```
fastapi_mysql  | Fatal glibc error: CPU does not support x86-64-v2
```

MySQL 8.0 требует инструкции x86-64-v2, которые не поддерживаются старыми процессорами.

## Решение

Основной `docker-compose.yml` теперь использует **MariaDB 10.5** вместо MySQL 8.0:
- ✅ Полностью совместим с MySQL
- ✅ Работает на старых процессорах
- ✅ Более легкий и оптимизированный
- ✅ Без изменений в коде приложения

## Что делать на сервере

### Шаг 1: Обновите код

```bash
git pull
```

### Шаг 2: Остановите старый контейнер

```bash
docker compose stop mysql
docker compose rm -f mysql
```

### Шаг 3: Запустите с новой конфигурацией

```bash
docker compose up -d mysql
```

### Шаг 4: Проверьте логи

```bash
docker compose logs -f mysql
```

Должно быть без ошибок про x86-64-v2.

## Альтернативные решения

### Вариант 1: Использовать скрипт автоматического исправления

```bash
./fix_mysql.sh
```

Выберите опцию 1 (стандартный метод с MariaDB 10.5).

### Вариант 2: Если нужен именно MySQL 5.7

```bash
docker compose -f docker-compose.mysql57.yml up -d mysql
```

⚠️ **Внимание**: MySQL 5.7 достиг End of Life. Используйте только если MariaDB не работает.

### Вариант 3: Очистить volumes и пересоздать

Если проблема сохраняется:

```bash
# Остановить и удалить
docker compose stop mysql
docker compose rm -f mysql

# Удалить volume (данные будут потеряны!)
docker volume rm $(docker volume ls -q | grep mysql)

# Запустить заново
docker compose up -d mysql
```

## Проверка

```bash
# Статус контейнера
docker compose ps mysql

# Должно быть: "Up" и "healthy"

# Проверка подключения
docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password -e "SHOW DATABASES;"
```

## Важные замечания

1. **MariaDB полностью совместим с MySQL** - никаких изменений в коде приложения не требуется
2. **Данные MySQL 8.0 несовместимы** - если у вас были данные в MySQL 8.0, их нужно экспортировать и импортировать заново
3. **Для новых проектов** - MariaDB используется по умолчанию для совместимости со старыми серверами

## Миграция данных (если были данные в MySQL 8.0)

Если у вас были данные в MySQL 8.0:

```bash
# 1. Экспорт данных (перед переходом на MariaDB)
docker exec fastapi_mysql mysqldump -u fastapi_user -pfastapi_password fastapi_auth > backup.sql

# 2. После перехода на MariaDB - импорт
docker exec -i fastapi_mysql mysql -u fastapi_user -pfastapi_password fastapi_auth < backup.sql
```

Но обычно проще просто пересоздать базу данных, если проект еще в разработке.

## Дополнительная информация

- Подробное руководство: [MYSQL_TROUBLESHOOTING.md](MYSQL_TROUBLESHOOTING.md)
- Быстрое исправление: [FIX_MYSQL_QUICK.md](FIX_MYSQL_QUICK.md)

