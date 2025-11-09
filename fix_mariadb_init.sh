#!/bin/bash

# Скрипт для исправления проблем с инициализацией MariaDB
# Использование: ./fix_mariadb_init.sh

set -e

echo "=========================================="
echo "Исправление проблем с MariaDB"
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

# Шаг 1: Остановка контейнеров
print_warning "Шаг 1: Остановка контейнеров..."
docker compose down
print_success "Контейнеры остановлены"

# Шаг 2: Удаление volume с данными
print_warning "Шаг 2: Удаление volume с данными MariaDB..."
print_warning "ВНИМАНИЕ: Все данные базы данных будут удалены!"
read -p "Продолжить? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Отменено пользователем"
    exit 1
fi

# Находим и удаляем volume
VOLUME_NAME=$(docker volume ls | grep mysql_data | awk '{print $2}' | head -1)
if [ -z "$VOLUME_NAME" ]; then
    VOLUME_NAME=$(docker volume ls | grep mariadb | awk '{print $2}' | head -1)
fi

if [ -n "$VOLUME_NAME" ]; then
    print_warning "Удаляем volume: $VOLUME_NAME"
    docker volume rm "$VOLUME_NAME" 2>/dev/null || print_warning "Volume уже удален или не найден"
    print_success "Volume удален"
else
    print_warning "Volume не найден, возможно уже удален"
fi

# Шаг 3: Очистка неиспользуемых volumes
print_warning "Шаг 3: Очистка неиспользуемых volumes..."
docker volume prune -f
print_success "Очистка завершена"

# Шаг 4: Запуск MySQL/MariaDB заново
print_warning "Шаг 4: Запуск MariaDB заново..."
docker compose up -d mysql

# Шаг 5: Ожидание инициализации
print_warning "Ожидание инициализации MariaDB (это может занять до 60 секунд)..."
sleep 10

for i in {1..12}; do
    STATUS=$(docker compose ps mysql | grep -o "Up\|healthy\|unhealthy" | head -1)
    if [[ "$STATUS" == *"healthy"* ]]; then
        print_success "MariaDB инициализирован и работает!"
        break
    fi
    if [ $i -eq 12 ]; then
        print_error "MariaDB не стал healthy за 60 секунд"
        echo "Проверьте логи:"
        echo "  docker compose logs mysql"
        exit 1
    fi
    echo "Ожидание... ($i/12)"
    sleep 5
done

# Шаг 6: Проверка логов
print_warning "Шаг 5: Проверка логов..."
docker compose logs mysql --tail=20

echo ""
echo "=========================================="
print_success "Исправление завершено!"
echo "=========================================="
echo ""
echo "Проверьте статус:"
echo "  docker compose ps mysql"
echo ""
echo "Проверьте логи:"
echo "  docker compose logs -f mysql"
echo ""

