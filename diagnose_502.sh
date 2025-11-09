#!/bin/bash

# Скрипт для диагностики ошибки 502 Bad Gateway
# Использование: ./diagnose_502.sh

echo "=========================================="
echo "Диагностика ошибки 502 Bad Gateway"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Проверка статуса контейнеров
echo "1. Проверка статуса контейнеров..."
docker compose ps
echo ""

# 2. Проверка логов FastAPI
echo "2. Последние логи FastAPI контейнера..."
docker compose logs fastapi --tail=50
echo ""

# 3. Проверка логов Nginx
echo "3. Последние логи Nginx контейнера..."
docker compose logs nginx --tail=50
echo ""

# 4. Проверка, что FastAPI слушает на порту 8000
echo "4. Проверка порта 8000 в контейнере FastAPI..."
if docker exec fastapi_app netstat -tuln 2>/dev/null | grep -q ":8000"; then
    print_success "FastAPI слушает на порту 8000"
    docker exec fastapi_app netstat -tuln | grep ":8000"
else
    print_error "FastAPI НЕ слушает на порту 8000"
    print_warning "Проверяем альтернативными методами..."
    docker exec fastapi_app ss -tuln 2>/dev/null | grep ":8000" || print_error "Порт 8000 не найден"
fi
echo ""

# 5. Проверка подключения из Nginx к FastAPI
echo "5. Проверка подключения из Nginx к FastAPI..."
if docker exec fastapi_nginx curl -s -o /dev/null -w "%{http_code}" http://fastapi:8000/health 2>/dev/null | grep -q "200"; then
    print_success "Nginx может подключиться к FastAPI"
else
    print_error "Nginx НЕ может подключиться к FastAPI"
    print_warning "Пробуем подключиться напрямую..."
    docker exec fastapi_nginx curl -v http://fastapi:8000/health 2>&1 | head -20
fi
echo ""

# 6. Проверка сети Docker
echo "6. Проверка сети Docker..."
docker network inspect backend_app_network 2>/dev/null | grep -A 10 "Containers" || print_warning "Сеть не найдена или контейнеры не подключены"
echo ""

# 7. Проверка DNS резолюции
echo "7. Проверка DNS резолюции в контейнере Nginx..."
docker exec fastapi_nginx nslookup fastapi 2>/dev/null || docker exec fastapi_nginx getent hosts fastapi 2>/dev/null || print_error "Не удалось разрешить имя fastapi"
echo ""

# 8. Проверка подключения к базе данных
echo "8. Проверка подключения FastAPI к базе данных..."
docker compose logs fastapi | grep -i "error\|exception\|failed" | tail -10 || print_warning "Ошибок подключения к БД не найдено в логах"
echo ""

# 9. Проверка healthcheck FastAPI
echo "9. Проверка healthcheck FastAPI..."
if docker exec fastapi_app curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "FastAPI healthcheck работает локально"
    docker exec fastapi_app curl -s http://localhost:8000/health | head -5
else
    print_error "FastAPI healthcheck НЕ работает"
fi
echo ""

# 10. Проверка портов хоста
echo "10. Проверка портов на хосте..."
if command -v netstat &> /dev/null; then
    netstat -tuln | grep -E ":80|:8000" || print_warning "Порты 80 и 8000 не найдены в netstat"
elif command -v ss &> /dev/null; then
    ss -tuln | grep -E ":80|:8000" || print_warning "Порты 80 и 8000 не найдены в ss"
fi
echo ""

# 11. Рекомендации
echo "=========================================="
echo "Рекомендации:"
echo "=========================================="
echo ""
print_warning "Если FastAPI не запускается:"
echo "  1. Проверьте логи: docker compose logs fastapi"
echo "  2. Проверьте подключение к БД"
echo "  3. Перезапустите контейнер: docker compose restart fastapi"
echo ""
print_warning "Если Nginx не может подключиться:"
echo "  1. Убедитесь, что контейнеры в одной сети"
echo "  2. Проверьте, что FastAPI слушает на 0.0.0.0:8000"
echo "  3. Перезапустите Nginx: docker compose restart nginx"
echo ""
print_warning "Для просмотра логов в реальном времени:"
echo "  docker compose logs -f fastapi nginx"
echo ""

