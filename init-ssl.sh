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
docker compose exec nginx chmod -R 755 /var/www/certbot

# Проверяем доступность домена
echo "🔍 Проверяем доступность домена $DOMAIN..."
if ! curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/.well-known/acme-challenge/test 2>/dev/null | grep -q "404\|403"; then
    echo "⚠️  Предупреждение: Домен может быть недоступен или nginx не настроен для ACME challenge"
    echo "Проверьте, что:"
    echo "  1. DNS запись для $DOMAIN указывает на IP сервера"
    echo "  2. Используется временная конфигурация nginx (nginx.conf.template)"
    echo "  3. Nginx запущен и доступен на порту 80"
fi

# Проверяем, что nginx может отдавать файлы из /var/www/certbot
echo "🔍 Проверяем конфигурацию nginx для ACME challenge..."
if ! docker compose exec nginx test -d /var/www/certbot; then
    echo "❌ Директория /var/www/certbot не существует в контейнере nginx"
    exit 1
fi

# Создаем тестовый файл для проверки
echo "test-file" | docker compose exec -T nginx tee /var/www/certbot/test.txt > /dev/null
if ! curl -s http://$DOMAIN/.well-known/acme-challenge/test.txt 2>/dev/null | grep -q "test-file"; then
    echo "⚠️  Предупреждение: Nginx не может отдавать файлы из /var/www/certbot"
    echo "Проверьте конфигурацию nginx - должен быть location /.well-known/acme-challenge/"
fi
docker compose exec nginx rm -f /var/www/certbot/test.txt

# Получаем сертификат
echo "🔐 Получаем SSL сертификат от Let's Encrypt..."
echo "Это может занять несколько минут..."
echo "Certbot будет проверять доступность домена через ACME challenge..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    -d $DOMAIN 2>&1 | tee /tmp/certbot-output.log

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
    echo ""
    echo "Последние строки вывода certbot:"
    tail -20 /tmp/certbot-output.log 2>/dev/null || echo "Лог недоступен"
    echo ""
    echo "Проверьте:"
    echo "  1. Логи certbot: docker compose logs certbot"
    echo "  2. Логи nginx: docker compose logs nginx"
    echo "  3. Доступность домена: curl -I http://$DOMAIN"
    echo "  4. ACME challenge: curl http://$DOMAIN/.well-known/acme-challenge/test"
    echo ""
    echo "Подробная инструкция по устранению проблем: см. TROUBLESHOOT_SSL.md"
    # Запускаем certbot обратно, даже если была ошибка
    docker compose up -d certbot 2>/dev/null || true
    exit 1
fi

