# Быстрое решение проблемы: CPU does not support x86-64-v2

## Проблема

```
Fatal glibc error: CPU does not support x86-64-v2
```

Эта ошибка возникает на старых серверах, процессор которых не поддерживает инструкции x86-64-v2.

## Решение 1: Использовать Python 3.11 (самое простое)

Обновленный `Dockerfile` уже использует Python 3.11. Просто пересоберите:

```bash
docker-compose build --no-cache
docker-compose up -d
```

## Решение 2: Использовать совместимый Dockerfile

Если Python 3.11 не помог, используйте максимально совместимый образ:

```bash
docker-compose -f docker-compose.compatible.yml build --no-cache
docker-compose -f docker-compose.compatible.yml up -d
```

## Решение 3: Установка без Docker (рекомендуется для старых серверов)

Если Docker не работает, установите напрямую на сервере:

```bash
# 1. Установите Python 3.10 или 3.11
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# 2. Запустите скрипт установки
chmod +x install.sh
./install.sh

# 3. Настройте .env файл
nano .env

# 4. Запустите приложение
source venv/bin/activate
python main.py
```

## Решение 4: Сборка на сервере

Соберите Docker-образ непосредственно на сервере:

```bash
docker build -f Dockerfile.server-build -t fastapi_app .
docker run -d -p 8000:8000 --env-file .env fastapi_app
```

## Проверка

После установки проверьте работу:

```bash
curl http://localhost:8000/docs
```

## Подробная документация

См. [DEPLOYMENT.md](DEPLOYMENT.md) для подробных инструкций.

