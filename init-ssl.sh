#!/bin/bash

# Скрипт для первоначального получения SSL сертификата через Certbot
# Использование: ./init-ssl.sh

set -e

DOMAIN="products.bunkov.in"
EMAIL="admin@bunkov.in"  # Замените на ваш email для уведомлений Let's Encrypt

echo "=========================================="
echo "Получение SSL сертификата для $DOMAIN"
echo "=========================================="

# Проверяем, что используется временная конфигурация
if ! grep -q "nginx.conf.template\|# Временный прокси" nginx/nginx.conf 2>/dev/null; then
    echo "⚠️  Внимание: Похоже, что используется конфигурация с HTTPS блоком"
    echo "Для получения сертификата нужна временная конфигурация без HTTPS"
    echo ""
    read -p "Продолжить? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Отменено. Используйте nginx.conf.template для первого запуска"
        exit 1
    fi
fi

# Проверяем, что контейнеры запущены
if ! docker compose ps | grep -q "fastapi_nginx.*Up"; then
    echo "❌ Контейнер fastapi_nginx не запущен"
    echo "Запустите сначала: docker compose up -d"
    exit 1
fi

# Останавливаем сервис certbot, если он запущен (чтобы не мешал получению первого сертификата)
echo "🛑 Останавливаем сервис certbot (если запущен)..."
docker compose stop certbot 2>/dev/null || true

# Создаем директорию для ACME challenge, если её нет
echo "📁 Создаем директорию для ACME challenge..."
docker compose exec nginx mkdir -p /var/www/certbot

# Получаем сертификат
echo "🔐 Получаем SSL сертификат от Let's Encrypt..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL сертификат успешно получен!"
    
    # Запускаем сервис certbot для автоматического обновления
    echo "🔄 Запускаем сервис certbot для автоматического обновления сертификатов..."
    docker compose up -d certbot
    
    echo ""
    echo "=========================================="
    echo "⚠️  ВАЖНО: Теперь нужно применить полную конфигурацию HTTPS"
    echo "=========================================="
    echo ""
    echo "Выполните следующие команды:"
    echo ""
    echo "1. Переключитесь на полную конфигурацию:"
    echo "   cp nginx/nginx.conf.https nginx/nginx.conf"
    echo ""
    echo "2. Пересоберите и перезапустите Nginx:"
    echo "   docker compose build nginx"
    echo "   docker compose up -d nginx"
    echo ""
    echo "3. Проверьте конфигурацию:"
    echo "   docker compose exec nginx nginx -t"
    echo ""
    echo "После этого сайт будет доступен по HTTPS:"
    echo "   https://$DOMAIN"
    echo ""
    echo "=========================================="
else
    echo "❌ Ошибка при получении сертификата"
    echo "Проверьте логи: docker compose logs certbot"
    # Запускаем certbot обратно, даже если была ошибка
    docker compose up -d certbot 2>/dev/null || true
    exit 1
fi

