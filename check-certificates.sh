#!/bin/bash

# Скрипт для проверки наличия SSL сертификатов (без зависаний)

echo "=========================================="
echo "Проверка SSL сертификатов"
echo "=========================================="
echo ""

# 1. Проверяем volume
echo "1. Проверка volume certbot_data..."
VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
if [ ! -z "$VOLUME_NAME" ]; then
    echo "   ✅ Volume найден: $VOLUME_NAME"
    
    # Проверяем файлы через временный контейнер alpine (быстро и надежно)
    echo ""
    echo "2. Проверка файлов сертификатов в volume..."
    CERT_DIR="/data/live/products.bunkov.in"
    
    # Используем alpine контейнер для проверки (не зависает)
    if docker run --rm -v ${VOLUME_NAME}:/data alpine test -d $CERT_DIR 2>/dev/null; then
        echo "   ✅ Директория сертификатов существует"
        echo ""
        echo "   Список файлов:"
        docker run --rm -v ${VOLUME_NAME}:/data alpine ls -la $CERT_DIR 2>/dev/null | head -10
        
        echo ""
        echo "   Проверка ключевых файлов:"
        for file in fullchain.pem privkey.pem chain.pem; do
            if docker run --rm -v ${VOLUME_NAME}:/data alpine test -f $CERT_DIR/$file 2>/dev/null; then
                echo "   ✅ $file существует"
            else
                echo "   ❌ $file не найден"
            fi
        done
        
        echo ""
        echo "   ✅ Сертификат получен! Можно применять HTTPS конфигурацию."
    else
        echo "   ❌ Директория сертификатов не найдена: $CERT_DIR"
        echo "   Сертификат еще не получен"
    fi
else
    echo "   ❌ Volume certbot_data не найден"
    echo "   Сертификат еще не получен"
fi

echo ""
echo "3. Проверка контейнеров..."
docker compose ps | grep -E "certbot|nginx" || echo "   Контейнеры не запущены"

echo ""
echo "=========================================="
echo "Проверка завершена"
echo "=========================================="
echo ""
echo "💡 Если сертификат найден, выполните:"
echo "   cp nginx/nginx.conf.https nginx/nginx.conf"
echo "   docker compose build nginx"
echo "   docker compose restart nginx"
echo ""
echo "💡 Если сертификат не найден, выполните:"
echo "   ./init-ssl.sh"
