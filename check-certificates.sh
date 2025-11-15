#!/bin/bash

# Скрипт для проверки наличия SSL сертификатов

echo "=========================================="
echo "Проверка SSL сертификатов"
echo "=========================================="
echo ""

# 1. Проверяем через volume
echo "1. Проверка сертификатов в volume certbot_data..."
if docker volume inspect products_backend_vibe_certbot_data > /dev/null 2>&1; then
    echo "   ✅ Volume certbot_data существует"
    
    # Пробуем проверить через временный контейнер certbot
    echo "   Проверяем сертификаты через certbot..."
    docker compose run --rm certbot certbot certificates 2>&1 | head -30
    
    # Проверяем файлы напрямую
    echo ""
    echo "   Проверяем файлы сертификатов..."
    CERT_PATH="/etc/letsencrypt/live/products.bunkov.in"
    if docker compose run --rm certbot test -d $CERT_PATH 2>/dev/null; then
        echo "   ✅ Директория сертификатов существует: $CERT_PATH"
        echo "   Список файлов:"
        docker compose run --rm certbot ls -la $CERT_PATH 2>/dev/null || echo "   Не удалось прочитать файлы"
    else
        echo "   ❌ Директория сертификатов не найдена: $CERT_PATH"
    fi
else
    echo "   ❌ Volume certbot_data не существует"
fi

echo ""
echo "2. Проверка через docker volume ls..."
docker volume ls | grep certbot

echo ""
echo "3. Проверка контейнеров certbot..."
docker compose ps certbot

echo ""
echo "=========================================="
echo "Проверка завершена"
echo "=========================================="

