#!/bin/bash

# Упрощенный скрипт для получения сертификата без docker compose run

DOMAIN="products.bunkov.in"
EMAIL="admin@bunkov.in"

echo "=========================================="
echo "Получение SSL сертификата (упрощенный способ)"
echo "=========================================="
echo ""

# Проверяем, что volumes существуют
VOLUME_CERTBOT_DATA=$(docker volume ls | grep certbot_data | awk '{print $2}')
VOLUME_CERTBOT_WWW=$(docker volume ls | grep certbot_www | awk '{print $2}')

if [ -z "$VOLUME_CERTBOT_DATA" ] || [ -z "$VOLUME_CERTBOT_WWW" ]; then
    echo "❌ Volumes не найдены. Создайте их:"
    echo "   docker volume create products_backend_vibe_certbot_data"
    echo "   docker volume create products_backend_vibe_certbot_www"
    exit 1
fi

echo "✅ Volumes найдены:"
echo "   certbot_data: $VOLUME_CERTBOT_DATA"
echo "   certbot_www: $VOLUME_CERTBOT_WWW"
echo ""

# Получаем сеть
NETWORK=$(docker network ls | grep app_network | awk '{print $1}')
if [ -z "$NETWORK" ]; then
    echo "❌ Сеть app_network не найдена"
    echo "   Запустите: docker compose up -d"
    exit 1
fi

echo "✅ Сеть найдена: $NETWORK"
echo ""

# Запускаем certbot напрямую через docker run (не через compose)
echo "🔐 Запускаем certbot для получения сертификата..."
echo ""

docker run --rm \
    --network ${NETWORK} \
    -v ${VOLUME_CERTBOT_DATA}:/etc/letsencrypt \
    -v ${VOLUME_CERTBOT_WWW}:/var/www/certbot \
    certbot/certbot:latest \
    certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL сертификат успешно получен!"
    echo ""
    echo "Теперь примените полную конфигурацию HTTPS:"
    echo "   cp nginx/nginx.conf.https nginx/nginx.conf"
    echo "   docker compose build nginx"
    echo "   docker compose restart nginx"
else
    echo ""
    echo "❌ Ошибка при получении сертификата"
    echo "Проверьте логи выше для деталей"
    exit 1
fi

