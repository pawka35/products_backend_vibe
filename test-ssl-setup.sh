#!/bin/bash

# Скрипт для проверки готовности к получению SSL сертификата

DOMAIN="products.bunkov.in"

echo "=========================================="
echo "Проверка готовности к получению SSL сертификата"
echo "=========================================="
echo ""

# 1. Проверка DNS
echo "1. Проверка DNS..."
DNS_IP=$(nslookup $DOMAIN 2>/dev/null | grep -A 1 "Name:" | tail -1 | awk '{print $2}')
if [ -z "$DNS_IP" ]; then
    echo "   ❌ DNS запись не найдена"
else
    echo "   ✅ DNS: $DOMAIN -> $DNS_IP"
fi
echo ""

# 2. Проверка доступности по HTTP (GET запрос)
echo "2. Проверка доступности по HTTP (GET)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "   ✅ HTTP доступен (код: $HTTP_CODE)"
else
    echo "   ⚠️  HTTP код: $HTTP_CODE"
    echo "   (405 Method Not Allowed для HEAD - это нормально, проверим GET)"
    # Проверяем GET запрос
    GET_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET http://$DOMAIN/)
    if [ "$GET_CODE" = "200" ] || [ "$GET_CODE" = "301" ] || [ "$GET_CODE" = "302" ]; then
        echo "   ✅ GET запрос работает (код: $GET_CODE)"
    else
        echo "   ❌ GET запрос не работает (код: $GET_CODE)"
    fi
fi
echo ""

# 3. Проверка ACME challenge endpoint
echo "3. Проверка ACME challenge endpoint..."
ACME_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/.well-known/acme-challenge/test)
if [ "$ACME_CODE" = "404" ]; then
    echo "   ✅ ACME challenge endpoint доступен (404 - файла нет, но endpoint работает)"
elif [ "$ACME_CODE" = "403" ]; then
    echo "   ⚠️  ACME challenge endpoint возвращает 403 (проверьте права доступа)"
else
    echo "   ⚠️  ACME challenge endpoint код: $ACME_CODE"
fi
echo ""

# 4. Проверка конфигурации nginx
echo "4. Проверка конфигурации nginx..."
if docker compose exec nginx nginx -t 2>&1 | grep -q "successful"; then
    echo "   ✅ Конфигурация nginx валидна"
else
    echo "   ❌ Ошибка в конфигурации nginx"
    docker compose exec nginx nginx -t
fi
echo ""

# 5. Проверка location для ACME challenge
echo "5. Проверка location для ACME challenge в nginx..."
if docker compose exec nginx grep -q "acme-challenge" /etc/nginx/nginx.conf; then
    echo "   ✅ Location /.well-known/acme-challenge/ найден в конфигурации"
    docker compose exec nginx grep -A 2 "acme-challenge" /etc/nginx/nginx.conf
else
    echo "   ❌ Location /.well-known/acme-challenge/ НЕ найден в конфигурации"
    echo "   Используйте временную конфигурацию: cp nginx/nginx.conf.template nginx/nginx.conf"
fi
echo ""

# 6. Проверка директории /var/www/certbot
echo "6. Проверка директории /var/www/certbot..."
if docker compose exec nginx test -d /var/www/certbot; then
    echo "   ✅ Директория /var/www/certbot существует"
    docker compose exec nginx ls -la /var/www/certbot | head -5
else
    echo "   ❌ Директория /var/www/certbot не существует"
    echo "   Создайте: docker compose exec nginx mkdir -p /var/www/certbot"
fi
echo ""

# 7. Тест записи и чтения файла
echo "7. Тест записи и чтения файла через ACME challenge..."
TEST_FILE="test-$(date +%s).txt"
echo "test-content" | docker compose exec -T nginx tee /var/www/certbot/$TEST_FILE > /dev/null 2>&1
if [ $? -eq 0 ]; then
    READ_CONTENT=$(curl -s http://$DOMAIN/.well-known/acme-challenge/$TEST_FILE)
    if [ "$READ_CONTENT" = "test-content" ]; then
        echo "   ✅ Файл успешно записан и прочитан через HTTP"
    else
        echo "   ⚠️  Файл записан, но не читается через HTTP"
        echo "   Содержимое: $READ_CONTENT"
    fi
    docker compose exec nginx rm -f /var/www/certbot/$TEST_FILE
else
    echo "   ❌ Не удалось записать файл в /var/www/certbot"
fi
echo ""

# 8. Проверка портов
echo "8. Проверка портов..."
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    echo "   ✅ Порт 80 открыт"
else
    echo "   ⚠️  Порт 80 не найден в netstat (может быть нормально, если используется другой способ)"
fi
echo ""

echo "=========================================="
echo "Проверка завершена"
echo "=========================================="
echo ""
echo "Если все проверки пройдены, можно запускать: ./init-ssl.sh"
echo "Если есть проблемы, см. TROUBLESHOOT_SSL.md"

