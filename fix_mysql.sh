#!/bin/bash

# Скрипт для автоматического исправления проблем с MySQL
# Использование: ./fix_mysql.sh

set -e

echo "=========================================="
echo "Автоматическое исправление MySQL"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Шаг 1: Остановка и удаление текущего контейнера
print_warning "Шаг 1: Остановка текущего MySQL контейнера..."
docker compose stop mysql 2>/dev/null || true
docker compose rm -f mysql 2>/dev/null || true
print_success "Контейнер остановлен"

# Шаг 2: Удаление volumes
read -p "Удалить данные MySQL (база данных будет пересоздана)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Шаг 2: Удаление volumes..."
    docker volume rm $(docker volume ls -q | grep mysql) 2>/dev/null || print_warning "Volumes не найдены или уже удалены"
    print_success "Volumes удалены"
else
    print_warning "Пропускаем удаление volumes (данные сохранены)"
fi

# Шаг 3: Выбор метода исправления
echo ""
echo "Выберите метод исправления:"
echo "1) Стандартный (MariaDB 10.5 - рекомендуется)"
echo "2) Исправленная конфигурация (MariaDB с оптимизациями)"
echo "3) MySQL 5.7 (для очень старых серверов, если MariaDB не работает)"
echo "4) Переключиться на существующий docker-compose.mariadb.yml"
read -p "Ваш выбор (1-4): " choice

case $choice in
    1)
        COMPOSE_FILE="docker-compose.yml"
        print_success "Выбран стандартный метод (MariaDB 10.5)"
        ;;
    2)
        COMPOSE_FILE="docker-compose.fix-mysql.yml"
        print_success "Выбрана исправленная конфигурация (MariaDB с оптимизациями)"
        ;;
    3)
        COMPOSE_FILE="docker-compose.mysql57.yml"
        print_warning "Используется MySQL 5.7 (End of Life, используйте только если MariaDB не работает)"
        print_success "Выбран MySQL 5.7"
        ;;
    4)
        COMPOSE_FILE="docker-compose.mariadb.yml"
        print_success "Выбран docker-compose.mariadb.yml"
        ;;
    *)
        print_error "Неверный выбор"
        exit 1
        ;;
esac

# Шаг 4: Запуск MySQL
print_warning "Шаг 3: Запуск MySQL с выбранной конфигурацией..."
docker compose -f $COMPOSE_FILE up -d mysql

# Шаг 5: Ожидание запуска
print_warning "Ожидание запуска MySQL (это может занять до 60 секунд)..."
sleep 5

# Проверка статуса
for i in {1..12}; do
    STATUS=$(docker compose -f $COMPOSE_FILE ps mysql | grep -o "Up\|healthy\|unhealthy" | head -1)
    if [[ "$STATUS" == *"healthy"* ]] || [[ "$STATUS" == *"Up"* ]]; then
        print_success "MySQL запущен!"
        break
    fi
    if [ $i -eq 12 ]; then
        print_error "MySQL не запустился за 60 секунд"
        echo "Проверьте логи:"
        echo "  docker compose -f $COMPOSE_FILE logs mysql"
        exit 1
    fi
    echo "Ожидание... ($i/12)"
    sleep 5
done

# Шаг 6: Проверка подключения
print_warning "Шаг 4: Проверка подключения к MySQL..."
sleep 5

if docker exec fastapi_mysql mysqladmin ping -h localhost -u fastapi_user -pfastapi_password --silent 2>/dev/null; then
    print_success "MySQL работает и доступен!"
else
    print_warning "MySQL запущен, но проверка подключения не удалась"
    print_warning "Это нормально, если MySQL еще инициализируется"
fi

# Шаг 7: Показать логи
echo ""
print_warning "Последние логи MySQL:"
docker compose -f $COMPOSE_FILE logs mysql --tail=20

echo ""
echo "=========================================="
print_success "Исправление завершено!"
echo "=========================================="
echo ""
echo "Проверьте статус:"
echo "  docker compose -f $COMPOSE_FILE ps mysql"
echo ""
echo "Проверьте логи:"
echo "  docker compose -f $COMPOSE_FILE logs -f mysql"
echo ""
echo "Подключитесь к MySQL:"
echo "  docker exec -it fastapi_mysql mysql -u fastapi_user -pfastapi_password fastapi_auth"
echo ""

