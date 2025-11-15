#!/bin/bash

# Скрипт для проверки автоматического обновления сертификатов

echo "=========================================="
echo "Проверка автоматического обновления сертификатов"
echo "=========================================="
echo ""

# 1. Проверяем статус сервиса certbot
echo "1. Проверка сервиса certbot..."
if docker compose ps certbot | grep -q "Up"; then
    echo "   ✅ Сервис certbot запущен"
    docker compose ps certbot | grep certbot
else
    echo "   ❌ Сервис certbot НЕ запущен!"
    echo "   Запустите: docker compose up -d certbot"
fi

# 2. Проверяем конфигурацию certbot в docker-compose.yml
echo ""
echo "2. Проверка конфигурации certbot..."
if grep -q "certbot renew" docker-compose.yml; then
    echo "   ✅ Автоматическое обновление настроено в docker-compose.yml"
    grep -A 5 "certbot:" docker-compose.yml | grep -A 3 "entrypoint"
else
    echo "   ⚠️  Автоматическое обновление не найдено в конфигурации"
fi

# 3. Проверяем срок действия сертификата
echo ""
echo "3. Проверка срока действия сертификата..."
VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
if [ ! -z "$VOLUME_NAME" ]; then
    CERT_FILE="/data/live/products.bunkov.in/fullchain.pem"
    if docker run --rm -v ${VOLUME_NAME}:/data alpine test -f $CERT_FILE 2>/dev/null; then
        echo "   ✅ Сертификат найден"
        echo "   Информация о сертификате:"
        # Пробуем получить информацию о сертификате
        docker run --rm -v ${VOLUME_NAME}:/data alpine openssl x509 -in $CERT_FILE -noout -dates 2>/dev/null || echo "   Не удалось прочитать информацию о сертификате"
    else
        echo "   ❌ Сертификат не найден"
    fi
else
    echo "   ❌ Volume certbot_data не найден"
fi

# 4. Проверяем логи certbot
echo ""
echo "4. Последние логи certbot (последние 20 строк)..."
if docker compose ps certbot | grep -q "Up"; then
    docker compose logs certbot --tail 20 2>&1 | sed 's/^/   /' || echo "   Логи недоступны"
else
    echo "   Сервис certbot не запущен, логи недоступны"
fi

# 5. Тест обновления (dry-run)
echo ""
echo "5. Тест обновления сертификата (dry-run)..."
echo "   Это проверит, может ли certbot обновить сертификат"
echo "   (реального обновления не произойдет)"
read -p "   Запустить тест? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
    VOLUME_WWW=$(docker volume ls | grep certbot_www | awk '{print $2}')
    NETWORK=$(docker network ls | grep app_network | awk '{print $1}')
    
    if [ ! -z "$VOLUME_NAME" ] && [ ! -z "$VOLUME_WWW" ] && [ ! -z "$NETWORK" ]; then
        echo "   Запускаем тест обновления..."
        docker run --rm \
            --network ${NETWORK} \
            -v ${VOLUME_NAME}:/etc/letsencrypt \
            -v ${VOLUME_WWW}:/var/www/certbot \
            certbot/certbot:latest \
            renew --dry-run 2>&1 | head -30
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            echo "   ✅ Тест обновления прошел успешно!"
        else
            echo "   ⚠️  Тест обновления показал проблемы"
        fi
    else
        echo "   ❌ Не найдены необходимые volumes или сеть"
    fi
fi

echo ""
echo "=========================================="
echo "Информация об автоматическом обновлении:"
echo "=========================================="
echo ""
echo "Certbot автоматически проверяет сертификаты каждые 12 часов"
echo "и обновляет их, если до истечения осталось менее 30 дней."
echo ""
echo "Сертификаты Let's Encrypt действительны 90 дней."
echo "Автоматическое обновление происходит за 30 дней до истечения."
echo ""
echo "Проверить статус можно командой:"
echo "   docker compose logs certbot | tail -20"
echo ""
echo "Принудительно обновить сертификат (если нужно):"
echo "   docker compose exec certbot certbot renew --force-renewal"
echo "   docker compose exec nginx nginx -s reload"
echo ""

