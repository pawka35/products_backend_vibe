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
    
    # Пробуем проверить через временный контейнер certbot (с таймаутом)
    echo "   Проверяем сертификаты через certbot (таймаут 10 секунд)..."
    timeout 10 docker compose run --rm certbot certbot certificates 2>&1 | head -30 || echo "   ⚠️  Команда зависла или превысила таймаут"
    
    # Проверяем файлы напрямую (быстрее, без зависаний)
    echo ""
    echo "   Проверяем файлы сертификатов напрямую..."
    CERT_PATH="/etc/letsencrypt/live/products.bunkov.in"
    
    # Проверяем через временный контейнер с таймаутом
    if timeout 5 docker compose run --rm certbot test -d $CERT_PATH 2>/dev/null; then
        echo "   ✅ Директория сертификатов существует: $CERT_PATH"
        echo "   Список файлов:"
        timeout 5 docker compose run --rm certbot ls -la $CERT_PATH 2>/dev/null || echo "   Не удалось прочитать файлы (таймаут)"
        
        # Проверяем наличие ключевых файлов
        echo ""
        echo "   Проверка ключевых файлов:"
        for file in fullchain.pem privkey.pem chain.pem; do
            if timeout 5 docker compose run --rm certbot test -f $CERT_PATH/$file 2>/dev/null; then
                echo "   ✅ $file существует"
            else
                echo "   ❌ $file не найден"
            fi
        done
    else
        echo "   ❌ Директория сертификатов не найдена: $CERT_PATH"
        echo "   Сертификат еще не получен"
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
echo "4. Быстрая проверка через volume (без certbot)..."
# Пробуем найти файлы сертификатов через монтирование volume
VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
if [ ! -z "$VOLUME_NAME" ]; then
    echo "   Volume: $VOLUME_NAME"
    # Пробуем проверить через временный контейнер с busybox
    if timeout 5 docker run --rm -v ${VOLUME_NAME}:/data alpine ls -la /data/live/products.bunkov.in/ 2>/dev/null | head -10; then
        echo "   ✅ Файлы сертификатов найдены в volume"
    else
        echo "   ❌ Файлы сертификатов не найдены в volume"
    fi
fi

echo ""
echo "=========================================="
echo "Проверка завершена"
echo "=========================================="
echo ""
echo "💡 Если команда certbot certificates зависает, это нормально."
echo "   Используйте проверку файлов напрямую (см. выше) - она быстрее и надежнее."

