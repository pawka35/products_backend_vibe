#!/bin/bash

# Скрипт для установки приложения напрямую на сервере (без Docker)
# Использование: ./install.sh

set -e

echo "=========================================="
echo "Установка FastAPI приложения"
echo "=========================================="

# Проверка Python
echo "1. Проверка Python..."
if ! command -v python3.10 &> /dev/null && ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.10 или 3.11 не найден"
    echo "Установите Python 3.10 или 3.11:"
    echo "  sudo apt update"
    echo "  sudo apt install python3.10 python3.10-venv python3-pip"
    exit 1
fi

# Определяем версию Python
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo "✅ Найден Python 3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD=python3.10
    echo "✅ Найден Python 3.10"
else
    PYTHON_CMD=python3
    echo "⚠️  Используется Python 3 (версия может быть несовместима)"
fi

# Создание виртуального окружения
echo ""
echo "2. Создание виртуального окружения..."
if [ -d "venv" ]; then
    echo "⚠️  Виртуальное окружение уже существует"
    read -p "Удалить и пересоздать? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        $PYTHON_CMD -m venv venv
    fi
else
    $PYTHON_CMD -m venv venv
fi

echo "✅ Виртуальное окружение создано"

# Активация виртуального окружения
echo ""
echo "3. Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo ""
echo "4. Обновление pip..."
pip install --upgrade pip setuptools wheel

# Установка зависимостей
echo ""
echo "5. Установка зависимостей..."
pip install -r requirements.txt

echo "✅ Зависимости установлены"

# Настройка переменных окружения
echo ""
echo "6. Настройка переменных окружения..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ Файл .env создан из env.example"
        echo "⚠️  Не забудьте отредактировать .env файл!"
    else
        echo "⚠️  Файл env.example не найден"
    fi
else
    echo "✅ Файл .env уже существует"
fi

# Проверка MySQL
echo ""
echo "7. Проверка подключения к MySQL..."
echo "⚠️  Убедитесь, что MySQL запущен и доступен"
echo "⚠️  Проверьте настройки DATABASE_URL в файле .env"

# Создание директорий
echo ""
echo "8. Создание необходимых директорий..."
mkdir -p logs
echo "✅ Директории созданы"

echo ""
echo "=========================================="
echo "✅ Установка завершена!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте файл .env и укажите правильные настройки"
echo "2. Активируйте виртуальное окружение: source venv/bin/activate"
echo "3. Запустите приложение: python main.py"
echo ""
echo "Или используйте systemd для автозапуска (см. DEPLOYMENT.md)"

