# Инструкция по развертыванию на сервере

## Проблема: CPU does not support x86-64-v2

Если вы получаете ошибку `Fatal glibc error: CPU does not support x86-64-v2`, это означает, что процессор сервера не поддерживает инструкции x86-64-v2, которые требуются для Python 3.12.

## Решения

### Решение 1: Использовать Python 3.11 (рекомендуется)

Обновленный `Dockerfile` использует Python 3.11, который совместим со старыми процессорами.

```bash
# Просто соберите и запустите
docker compose build
docker compose up -d
```

### Решение 2: Использовать максимально совместимый образ

Если Python 3.11 не работает, используйте `Dockerfile.compatible`:

```bash
# Сборка с альтернативным Dockerfile
docker build -f Dockerfile.compatible -t fastapi_app .
docker compose up -d
```

Или обновите `docker compose.yml`:

```yaml
fastapi:
  build:
    context: .
    dockerfile: Dockerfile.compatible
  # ... остальные настройки
```

### Решение 3: Сборка непосредственно на сервере

Соберите Docker-образ непосредственно на сервере, чтобы гарантировать совместимость:

```bash
# Используйте Dockerfile.server-build
docker build -f Dockerfile.server-build -t fastapi_app .
docker compose up -d
```

### Решение 4: Установка без Docker (напрямую на сервере)

Если Docker не решает проблему, установите приложение напрямую на сервере:

```bash
# 1. Установите Python 3.10 или 3.11
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# 2. Создайте виртуальное окружение
python3.10 -m venv venv
source venv/bin/activate

# 3. Установите зависимости
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 4. Настройте переменные окружения
cp env.example .env
# Отредактируйте .env файл

# 5. Запустите приложение
python main.py
```

Или используйте systemd для автозапуска:

```bash
# Создайте файл /etc/systemd/system/fastapi.service
sudo nano /etc/systemd/system/fastapi.service
```

Содержимое файла:

```ini
[Unit]
Description=FastAPI Application
After=network.target mysql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/app
Environment="PATH=/path/to/your/app/venv/bin"
ExecStart=/path/to/your/app/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
```

## Проверка совместимости CPU

Чтобы проверить, какие инструкции поддерживает ваш процессор:

```bash
# Проверка поддержки x86-64-v2
grep flags /proc/cpuinfo | head -1 | grep -o 'sse3\|ssse3\|sse4_1\|sse4_2\|popcnt'

# Если команда не выводит все эти флаги, CPU не поддерживает x86-64-v2
```

## Рекомендации

1. **Для новых серверов**: Используйте стандартный `Dockerfile` с Python 3.11
2. **Для старых серверов**: Используйте `Dockerfile.compatible` или `Dockerfile.server-build`
3. **Для максимальной совместимости**: Установите напрямую на сервере без Docker

## Отладка

Если проблема сохраняется:

1. Проверьте версию glibc на сервере:
   ```bash
   ldd --version
   ```

2. Проверьте архитектуру процессора:
   ```bash
   uname -m
   cat /proc/cpuinfo | grep "model name" | head -1
   ```

3. Проверьте логи Docker:
   ```bash
   docker compose logs fastapi
   ```

4. Попробуйте запустить Python напрямую:
   ```bash
   docker run --rm python:3.11-slim python --version
   ```

## Альтернативные варианты

### Использование PyPy

PyPy может быть более совместимым на старых системах:

```dockerfile
FROM pypy:3.10-slim
# ... остальное
```

### Использование Alpine Linux

Alpine Linux использует musl libc вместо glibc, что может решить проблему:

```dockerfile
FROM python:3.11-alpine
# ... остальное
```

Однако учтите, что некоторые Python-пакеты могут не работать с musl libc.

