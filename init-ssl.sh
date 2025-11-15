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
    echo "Переключаемся на временную конфигурацию..."
    cp nginx/nginx.conf.template nginx/nginx.conf
    echo "✅ Временная конфигурация применена"
    echo "Пересобираем и перезапускаем nginx..."
    docker compose build nginx
    docker compose up -d nginx
    echo "⏳ Ждем запуска nginx..."
    sleep 5
    echo "✅ Nginx перезапущен"
fi

# Проверяем, что конфигурация nginx в контейнере правильная
echo "🔍 Проверяем конфигурацию nginx в контейнере..."
if ! docker compose exec nginx grep -q "acme-challenge" /etc/nginx/nginx.conf 2>/dev/null; then
    echo "❌ Location /.well-known/acme-challenge/ не найден в конфигурации nginx!"
    echo "Пересоберите nginx: docker compose build nginx && docker compose up -d nginx"
    exit 1
fi
echo "   ✅ Location /.well-known/acme-challenge/ найден в конфигурации"

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
# Проверяем GET запрос (certbot использует GET, а не HEAD)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/ 2>/dev/null)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "   ✅ Домен доступен по HTTP (код: $HTTP_CODE)"
else
    echo "   ⚠️  HTTP код: $HTTP_CODE (405 для HEAD - это нормально, проверяем GET)"
    # Проверяем GET запрос явно
    GET_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://$DOMAIN/ 2>/dev/null)
    if [ "$GET_CODE" = "200" ] || [ "$GET_CODE" = "301" ] || [ "$GET_CODE" = "302" ]; then
        echo "   ✅ GET запрос работает (код: $GET_CODE)"
    else
        echo "   ⚠️  GET запрос вернул код: $GET_CODE"
        echo "   Проверьте, что:"
        echo "     1. DNS запись для $DOMAIN указывает на IP сервера"
        echo "     2. Используется временная конфигурация nginx (nginx.conf.template)"
        echo "     3. Nginx запущен и доступен на порту 80"
    fi
fi

# Проверяем, что nginx может отдавать файлы из /var/www/certbot
echo "🔍 Проверяем конфигурацию nginx для ACME challenge..."
if ! docker compose exec nginx test -d /var/www/certbot; then
    echo "❌ Директория /var/www/certbot не существует в контейнере nginx"
    exit 1
fi

# Создаем тестовый файл для проверки
echo "🔍 Тестируем ACME challenge endpoint..."
# Certbot записывает файлы в /var/www/certbot/.well-known/acme-challenge/
TEST_DIR="/var/www/certbot/.well-known/acme-challenge"
TEST_FILE="test-$(date +%s).txt"
docker compose exec nginx mkdir -p $TEST_DIR 2>/dev/null || true
echo "test-content" | docker compose exec -T nginx tee $TEST_DIR/$TEST_FILE > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # Проверяем, что файл действительно создан
    if docker compose exec nginx test -f $TEST_DIR/$TEST_FILE; then
        echo "   ✅ Файл создан: $TEST_DIR/$TEST_FILE"
        # Проверяем содержимое файла
        FILE_CONTENT=$(docker compose exec nginx cat $TEST_DIR/$TEST_FILE 2>/dev/null)
        echo "   Содержимое файла в контейнере: '$FILE_CONTENT'"
        
        # Пробуем прочитать через HTTP
        READ_CONTENT=$(curl -s http://$DOMAIN/.well-known/acme-challenge/$TEST_FILE 2>/dev/null)
        if [ "$READ_CONTENT" = "test-content" ]; then
            echo "   ✅ ACME challenge endpoint работает - файл успешно прочитан через HTTP"
        else
            echo "   ⚠️  ACME challenge endpoint: файл записан, но не читается через HTTP"
            echo "   Получено через HTTP: '$READ_CONTENT'"
            echo "   Ожидалось: 'test-content'"
            echo ""
            echo "   Проверяем конфигурацию nginx в контейнере:"
            docker compose exec nginx grep -A 3 "acme-challenge" /etc/nginx/nginx.conf
            echo ""
            echo "   Проверяем логи nginx:"
            docker compose exec nginx tail -3 /var/log/nginx/error.log 2>/dev/null || echo "   Логи недоступны"
            echo ""
            echo "   Попробуйте:"
            echo "   1. Пересобрать nginx: docker compose build nginx"
            echo "   2. Перезапустить nginx: docker compose restart nginx"
            echo "   3. Проверить конфигурацию: docker compose exec nginx nginx -t"
        fi
    else
        echo "   ❌ Файл не найден после создания: $TEST_DIR/$TEST_FILE"
    fi
    docker compose exec nginx rm -f $TEST_DIR/$TEST_FILE
else
    echo "   ⚠️  Не удалось записать тестовый файл в $TEST_DIR"
    echo "   Проверьте права доступа к volume certbot_www"
fi

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

