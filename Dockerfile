# Используем Python 3.11 для лучшей совместимости со старыми процессорами
# Python 3.11 собирается для более старых архитектур x86-64
FROM python:3.11-slim as builder

# Устанавливаем системные зависимости для компиляции
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Устанавливаем runtime зависимости
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    libffi8 \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение из builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app
USER app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем код приложения
COPY --chown=app:app . .

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["python", "main.py"]
