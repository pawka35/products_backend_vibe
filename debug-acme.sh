#!/bin/bash

# Скрипт для диагностики проблемы с ACME challenge

DOMAIN="products.bunkov.in"

echo "=========================================="
echo "Диагностика ACME challenge endpoint"
echo "=========================================="
echo ""

# 1. Проверяем текущую конфигурацию nginx
echo "1. Проверка конфигурации nginx..."
echo "   Текущий файл конфигурации:"
docker compose exec nginx cat /etc/nginx/nginx.conf | grep -A 5 "acme-challenge" || echo "   ❌ Location не найден!"
echo ""

# 2. Проверяем, что директория существует
echo "2. Проверка директорий..."
echo "   /var/www/certbot:"
docker compose exec nginx ls -la /var/www/certbot 2>/dev/null || echo "   ❌ Директория не существует"
echo ""
echo "   /var/www/certbot/.well-known/acme-challenge:"
docker compose exec nginx ls -la /var/www/certbot/.well-known/acme-challenge 2>/dev/null || echo "   ❌ Директория не существует"
echo ""

# 3. Создаем тестовый файл и проверяем его путь
echo "3. Создание тестового файла..."
TEST_DIR="/var/www/certbot/.well-known/acme-challenge"
TEST_FILE="debug-test-$(date +%s).txt"
docker compose exec nginx mkdir -p $TEST_DIR 2>/dev/null || true
echo "test-content-123" | docker compose exec -T nginx tee $TEST_DIR/$TEST_FILE > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Файл создан: $TEST_DIR/$TEST_FILE"
    echo "   Проверяем содержимое файла в контейнере:"
    docker compose exec nginx cat $TEST_DIR/$TEST_FILE
    echo ""
    echo "   Проверяем путь, который должен искать nginx:"
    echo "   Запрос: http://$DOMAIN/.well-known/acme-challenge/$TEST_FILE"
    echo "   Nginx должен искать: /var/www/certbot/.well-known/acme-challenge/$TEST_FILE"
    echo ""
    echo "   Проверяем, существует ли файл по этому пути:"
    docker compose exec nginx test -f /var/www/certbot/.well-known/acme-challenge/$TEST_FILE && echo "   ✅ Файл существует" || echo "   ❌ Файл не существует"
    echo ""
    echo "   Пробуем прочитать через HTTP:"
    HTTP_RESPONSE=$(curl -s http://$DOMAIN/.well-known/acme-challenge/$TEST_FILE)
    echo "   Ответ: $HTTP_RESPONSE"
    echo ""
    echo "   Проверяем логи nginx:"
    docker compose exec nginx tail -5 /var/log/nginx/error.log 2>/dev/null || echo "   Логи недоступны"
    echo ""
    
    # Удаляем тестовый файл
    docker compose exec nginx rm -f $TEST_DIR/$TEST_FILE
else
    echo "   ❌ Не удалось создать файл"
fi

echo ""
echo "4. Проверка конфигурации nginx (детально)..."
docker compose exec nginx nginx -T 2>/dev/null | grep -A 10 "acme-challenge" || echo "   ❌ Location не найден в конфигурации"
echo ""

echo "5. Проверка, какой конфигурационный файл используется..."
docker compose exec nginx ls -la /etc/nginx/nginx.conf
echo ""

echo "=========================================="
echo "Диагностика завершена"
echo "=========================================="

