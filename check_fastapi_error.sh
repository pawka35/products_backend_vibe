#!/bin/bash

# Скрипт для проверки ошибок FastAPI контейнера
# Использование: ./check_fastapi_error.sh

echo "=========================================="
echo "Проверка ошибок FastAPI контейнера"
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

# 1. Проверка статуса контейнера
echo "1. Статус контейнера fastapi_app..."
docker compose ps fastapi
echo ""

# 2. Полные логи FastAPI
echo "2. Полные логи FastAPI контейнера..."
docker compose logs fastapi --tail=100
echo ""

# 3. Попытка запуска контейнера
echo "3. Попытка запуска контейнера..."
docker compose up fastapi 2>&1 | head -50
echo ""

# 4. Проверка образа
echo "4. Проверка образа..."
docker images | grep products_backend_vibe-fastapi || docker images | grep fastapi
echo ""

# 5. Проверка переменных окружения
echo "5. Проверка переменных окружения..."
docker compose config | grep -A 20 "fastapi:"
echo ""

# 6. Проверка подключения к БД
echo "6. Проверка подключения к БД..."
docker compose ps mysql
echo ""

# 7. Попытка запуска контейнера вручную для просмотра ошибок
echo "7. Попытка запуска контейнера в интерактивном режиме..."
print_warning "Останавливаем контейнер..."
docker compose stop fastapi 2>/dev/null || true
print_warning "Запускаем для просмотра ошибок (Ctrl+C для остановки)..."
docker compose up fastapi

