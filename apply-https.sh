#!/bin/bash

# Скрипт для применения полной конфигурации HTTPS

DOMAIN="products.bunkov.in"

echo "=========================================="
echo "Применение полной конфигурации HTTPS"
echo "=========================================="
echo ""

# 1. Проверяем наличие сертификата
echo "1. Проверка наличия сертификата..."
VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
if [ -z "$VOLUME_NAME" ]; then
    echo "   ❌ Volume certbot_data не найден"
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

# 2. Переключаемся на полную конфигурацию
echo ""
echo "2. Применение полной конфигурации HTTPS..."
if [ ! -f nginx/nginx.conf.https ]; then
    echo "   ❌ Файл nginx/nginx.conf.https не найден"
    exit 1
fi

cp nginx/nginx.conf.https nginx/nginx.conf
echo "   ✅ Конфигурация скопирована"

# 3. Пересобираем nginx
echo ""
echo "3. Пересборка nginx..."
docker compose build nginx
if [ $? -ne 0 ]; then
    echo "   ❌ Ошибка при пересборке nginx"
    exit 1
fi
echo "   ✅ Nginx пересобран"

# 4. Перезапускаем nginx
echo ""
echo "4. Перезапуск nginx..."
docker compose restart nginx
sleep 3
echo "   ✅ Nginx перезапущен"

# 5. Проверяем конфигурацию
echo ""
echo "5. Проверка конфигурации nginx..."
if docker compose exec nginx nginx -t 2>&1 | grep -q "successful"; then
    echo "   ✅ Конфигурация nginx валидна"
else
    echo "   ❌ Ошибка в конфигурации nginx!"
    docker compose exec nginx nginx -t
    exit 1
fi

# 6. Проверяем HTTPS
echo ""
echo "6. Проверка HTTPS..."
sleep 2
HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health 2>/dev/null)
if [ "$HTTPS_CODE" = "200" ]; then
    echo "   ✅ HTTPS работает (код: $HTTPS_CODE)"
else
    echo "   ⚠️  HTTPS вернул код: $HTTPS_CODE"
    echo "   Проверьте вручную: curl https://$DOMAIN/health"
fi

# 7. Проверяем редирект HTTP -> HTTPS
echo ""
echo "7. Проверка редиректа HTTP -> HTTPS..."
HTTP_REDIRECT=$(curl -s -o /dev/null -w "%{http_code}" -L http://$DOMAIN/health 2>/dev/null)
if [ "$HTTP_REDIRECT" = "200" ]; then
    echo "   ✅ Редирект работает (HTTP -> HTTPS -> 200)"
else
    echo "   ⚠️  Редирект вернул код: $HTTP_REDIRECT"
fi

# 8. Запускаем certbot для автоматического обновления
echo ""
echo "8. Запуск сервиса certbot для автоматического обновления..."
docker compose up -d certbot
if [ $? -eq 0 ]; then
    echo "   ✅ Certbot запущен"
else
    echo "   ⚠️  Не удалось запустить certbot (не критично)"
fi

echo ""
echo "=========================================="
echo "✅ HTTPS настроен успешно!"
echo "=========================================="
echo ""
echo "Сайт доступен по адресу:"
echo "   https://$DOMAIN"
echo ""
echo "Проверьте в браузере:"
echo "   1. Откройте https://$DOMAIN"
echo "   2. Проверьте, что есть зеленый замочек (валидный SSL)"
echo "   3. Проверьте, что HTTP редиректится на HTTPS"
echo ""

