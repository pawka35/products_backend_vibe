#!/bin/bash

# Быстрый тест ACME challenge endpoint

DOMAIN="products.bunkov.in"

echo "=========================================="
echo "Быстрый тест ACME challenge endpoint"
echo "=========================================="
echo ""

# 1. Проверяем конфигурацию nginx
echo "1. Проверка конфигурации nginx..."
if docker compose exec nginx grep -q "acme-challenge" /etc/nginx/nginx.conf 2>/dev/null; then
    echo "   ✅ Location /.well-known/acme-challenge/ найден"
    docker compose exec nginx grep -A 3 "acme-challenge" /etc/nginx/nginx.conf
else
    echo "   ❌ Location /.well-known/acme-challenge/ НЕ найден!"
    echo "   Нужно переключиться на временную конфигурацию:"
    echo "   cp nginx/nginx.conf.template nginx/nginx.conf"
    echo "   docker compose build nginx"
    echo "   docker compose restart nginx"
    exit 1
fi

echo ""
echo "2. Создание тестового файла..."
TEST_DIR="/var/www/certbot/.well-known/acme-challenge"
TEST_FILE="quick-test-$(date +%s).txt"
docker compose exec nginx mkdir -p $TEST_DIR 2>/dev/null || true
echo "test-content-$(date +%s)" | docker compose exec -T nginx tee $TEST_DIR/$TEST_FILE > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Файл создан: $TEST_DIR/$TEST_FILE"
    
    # Проверяем содержимое в контейнере
    FILE_CONTENT=$(docker compose exec nginx cat $TEST_DIR/$TEST_FILE 2>/dev/null)
    echo "   Содержимое в контейнере: '$FILE_CONTENT'"
    
    echo ""
    echo "3. Проверка через HTTP..."
    HTTP_RESPONSE=$(curl -s http://$DOMAIN/.well-known/acme-challenge/$TEST_FILE)
    echo "   Ответ HTTP: '$HTTP_RESPONSE'"
    
    if [ "$HTTP_RESPONSE" = "$FILE_CONTENT" ]; then
        echo "   ✅ ACME challenge endpoint работает правильно!"
        echo "   ✅ Файл успешно прочитан через HTTP"
    else
        echo "   ❌ ACME challenge endpoint НЕ работает!"
        echo "   Ожидалось: '$FILE_CONTENT'"
        echo "   Получено: '$HTTP_RESPONSE'"
        echo ""
        echo "   Проверьте:"
        echo "   1. Конфигурация nginx перезагружена?"
        echo "   2. Используется временная конфигурация (nginx.conf.template)?"
        echo "   3. Volume certbot_www правильно монтирован?"
    fi
    
    # Удаляем тестовый файл
    docker compose exec nginx rm -f $TEST_DIR/$TEST_FILE
else
    echo "   ❌ Не удалось создать файл"
fi

echo ""
echo "=========================================="
echo "Тест завершен"
echo "=========================================="

