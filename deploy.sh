#!/bin/bash

# Скрипт для деплоя изменений на продакшен сервер
# Использование: ./deploy.sh

set -e

echo "=========================================="
echo "🚀 Деплой на продакшен"
echo "=========================================="
echo ""

# Проверяем, что мы на ветке main
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Внимание: вы не на ветке main (текущая ветка: $CURRENT_BRANCH)"
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "1. Обновление кода из репозитория..."
git pull origin main
echo "   ✅ Код обновлен"
echo ""

echo "2. Выполнение миграций базы данных (если есть)..."
# Проверяем наличие новых миграций
if [ -f "migrations/add_telegram_notifications.py" ]; then
    echo "   Найдена миграция add_telegram_notifications.py"
    read -p "   Выполнить миграцию? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Выполняем миграцию внутри контейнера
        docker compose exec fastapi python3 migrations/add_telegram_notifications.py || {
            echo "   ⚠️  Не удалось выполнить миграцию в контейнере, пробуем локально..."
            source venv/bin/activate && python3 migrations/add_telegram_notifications.py
        }
        echo "   ✅ Миграция выполнена"
    fi
fi
echo ""

echo "3. Пересборка контейнеров..."
docker compose build
echo "   ✅ Контейнеры пересобраны"
echo ""

echo "4. Перезапуск сервисов..."
docker compose up -d
echo "   ✅ Сервисы перезапущены"
echo ""

echo "5. Проверка статуса контейнеров..."
sleep 5  # Даем время на запуск
docker compose ps
echo ""

echo "6. Проверка логов (последние 20 строк)..."
echo "   Логи FastAPI:"
docker compose logs --tail=20 fastapi
echo ""

echo "=========================================="
echo "✅ Деплой завершен!"
echo "=========================================="
echo ""
echo "Проверьте работу приложения:"
echo "  - Health check: curl https://products.bunkov.in/health"
echo "  - API docs: https://products.bunkov.in/docs"
echo ""

