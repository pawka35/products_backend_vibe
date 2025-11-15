#!/bin/bash

# Скрипт для запуска сервиса certbot для автоматического обновления

echo "=========================================="
echo "Запуск сервиса certbot для автоматического обновления"
echo "=========================================="
echo ""

# 1. Проверяем наличие сертификата
echo "1. Проверка наличия сертификата..."
VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
if [ -z "$VOLUME_NAME" ]; then
    echo "   ❌ Volume certbot_data не найден"
    echo "   Сначала получите сертификат: ./get-cert-simple.sh"
    exit 1
fi

CERT_DIR="/data/live/products.bunkov.in"
if docker run --rm -v ${VOLUME_NAME}:/data alpine test -f $CERT_DIR/fullchain.pem 2>/dev/null; then
    echo "   ✅ Сертификат найден"
else
    echo "   ❌ Сертификат не найден!"
    echo "   Сначала получите сертификат: ./get-cert-simple.sh"
    exit 1
fi

# 2. Запускаем сервис certbot
echo ""
echo "2. Запуск сервиса certbot..."
docker compose up -d certbot

if [ $? -eq 0 ]; then
    echo "   ✅ Сервис certbot запущен"
else
    echo "   ❌ Ошибка при запуске certbot"
    exit 1
fi

# 3. Проверяем статус
echo ""
echo "3. Проверка статуса..."
sleep 2
if docker compose ps certbot | grep -q "Up"; then
    echo "   ✅ Certbot работает"
    docker compose ps certbot | grep certbot
else
    echo "   ⚠️  Certbot не запустился, проверьте логи:"
    echo "   docker compose logs certbot"
fi

# 4. Проверяем логи
echo ""
echo "4. Последние логи certbot..."
docker compose logs certbot --tail 10 2>&1 | sed 's/^/   /' || echo "   Логи недоступны"

echo ""
echo "=========================================="
echo "✅ Сервис certbot запущен!"
echo "=========================================="
echo ""
echo "Certbot будет автоматически проверять и обновлять сертификаты"
echo "каждые 12 часов."
echo ""
echo "Проверить статус:"
echo "   docker compose ps certbot"
echo ""
echo "Посмотреть логи:"
echo "   docker compose logs certbot | tail -20"
echo ""

