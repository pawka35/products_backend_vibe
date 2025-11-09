#!/bin/bash

# Скрипт для быстрой проверки логов FastAPI
# Использование: ./check_fastapi_logs.sh

echo "=========================================="
echo "Проверка логов FastAPI"
echo "=========================================="
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Статус контейнера
echo "1. Статус контейнера fastapi_app:"
docker compose ps fastapi
echo ""

# 2. Последние 100 строк логов
echo "2. Последние 100 строк логов FastAPI:"
echo "----------------------------------------"
docker compose logs fastapi --tail=100
echo "----------------------------------------"
echo ""

# 3. Поиск ошибок
echo "3. Поиск ошибок в логах:"
echo "----------------------------------------"
docker compose logs fastapi | grep -i "error\|exception\|traceback\|failed" | tail -20
echo "----------------------------------------"
echo ""

# 4. Попытка запуска в foreground
echo "4. Попытка запуска контейнера для просмотра ошибок:"
print_warning "Останавливаем контейнер..."
docker compose stop fastapi 2>/dev/null || true
print_warning "Запускаем в foreground (последние 50 строк)..."
timeout 30 docker compose up fastapi 2>&1 | tail -50 || true
echo ""

# 5. Проверка подключения к БД
echo "5. Проверка подключения к базе данных:"
print_warning "Проверяем, может ли FastAPI подключиться к БД..."
docker compose exec -T mysql mysql -u fastapi_user -pfastapi_password -e "SELECT 1;" fastapi_auth 2>&1 | head -5
echo ""

# 6. Проверка переменных окружения
echo "6. Проверка переменных окружения:"
docker compose config | grep -A 15 "fastapi:" | grep -E "DATABASE_URL|SECRET_KEY" || echo "Переменные не найдены в конфиге"
echo ""

print_warning "Для просмотра логов в реальном времени используйте:"
echo "  docker compose logs -f fastapi"
echo ""

