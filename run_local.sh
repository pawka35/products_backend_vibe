#!/bin/bash

# Скрипт для локального запуска приложения (для разработки)
# Использование: ./run_local.sh

set -e

echo "=========================================="
echo "🚀 Локальный запуск FastAPI приложения"
echo "=========================================="
echo ""

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "Создайте его: python3 -m venv venv"
    exit 1
fi

# Активируем виртуальное окружение
echo "1. Активируем виртуальное окружение..."
source venv/bin/activate

# Проверяем зависимости
echo "2. Проверяем зависимости..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "   ⚠️  Зависимости не установлены, устанавливаем..."
    pip install -r requirements.txt
fi
echo "   ✅ Зависимости установлены"
echo ""

# Проверяем .env файл
if [ ! -f ".env" ]; then
    echo "3. Создаем .env файл из примера..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "   ✅ .env файл создан из env.example"
        echo "   ⚠️  Отредактируйте .env файл и укажите правильные настройки!"
    else
        echo "   ⚠️  Файл env.example не найден"
        echo "   Создайте .env файл вручную"
    fi
else
    echo "3. ✅ .env файл найден"
fi
echo ""

# Проверяем подключение к БД
echo "4. Проверяем подключение к базе данных..."
python3 << 'EOF'
from database import wait_for_database
if wait_for_database(max_retries=3, retry_delay=1):
    print('   ✅ Подключение к БД успешно')
else:
    print('   ⚠️  Не удалось подключиться к БД')
    print('   Убедитесь, что:')
    print('   - MySQL/MariaDB запущен')
    print('   - DATABASE_URL в .env правильный')
    print('   - База данных создана')
EOF
echo ""

# Выполняем миграции (если нужно)
echo "5. Проверяем миграции..."
if [ -f "migrations/add_telegram_notifications.py" ]; then
    read -p "   Выполнить миграцию add_telegram_notifications? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 migrations/add_telegram_notifications.py
    fi
fi
echo ""

# Запускаем приложение
echo "6. Запускаем приложение..."
echo "   Приложение будет доступно по адресу: http://localhost:8000"
echo "   API документация: http://localhost:8000/docs"
echo "   ReDoc: http://localhost:8000/redoc"
echo ""
echo "   Для остановки нажмите Ctrl+C"
echo ""
echo "=========================================="

# Запускаем uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

