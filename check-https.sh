#!/bin/bash

# Скрипт для проверки HTTPS

DOMAIN="products.bunkov.in"

echo "=========================================="
echo "Проверка HTTPS"
echo "=========================================="
echo ""

# 1. Проверяем конфигурацию nginx
echo "1. Проверка конфигурации nginx..."
if docker compose exec nginx grep -q "listen 443" /etc/nginx/nginx.conf 2>/dev/null; then
    echo "   ✅ Конфигурация HTTPS найдена в nginx.conf"
    docker compose exec nginx grep "listen 443" /etc/nginx/nginx.conf
else
    echo "   ❌ Конфигурация HTTPS НЕ найдена!"
    echo "   Нужно применить полную конфигурацию: ./apply-https.sh"
fi

# 2. Проверяем, слушает ли nginx на порту 443
echo ""
echo "2. Проверка порта 443 в контейнере nginx..."
if docker compose exec nginx netstat -tuln 2>/dev/null | grep -q ":443 "; then
    echo "   ✅ Nginx слушает на порту 443"
    docker compose exec nginx netstat -tuln | grep ":443"
else
    echo "   ❌ Nginx НЕ слушает на порту 443!"
    echo "   Проверьте конфигурацию и перезапустите nginx"
fi

# 3. Проверяем порт 443 на хосте
echo ""
echo "3. Проверка порта 443 на хосте..."
if netstat -tuln 2>/dev/null | grep -q ":443 "; then
    echo "   ✅ Порт 443 слушается на хосте"
elif ss -tuln 2>/dev/null | grep -q ":443 "; then
    echo "   ✅ Порт 443 слушается на хосте (через ss)"
elif docker compose ps nginx | grep -q "Up"; then
    echo "   ⚠️  netstat не показывает порт 443 (Docker пробрасывает через iptables)"
    echo "   Проверьте docker compose ps nginx"
fi

# 4. Проверяем firewall
echo ""
echo "4. Проверка firewall..."
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "443/tcp.*ALLOW"; then
        echo "   ✅ Порт 443 открыт в firewall"
    else
        echo "   ⚠️  Порт 443 может быть закрыт в firewall"
        echo "   Откройте: sudo ufw allow 443/tcp"
    fi
fi

# 5. Проверяем наличие сертификатов
echo ""
echo "5. Проверка сертификатов..."
VOLUME_NAME=$(docker volume ls | grep certbot_data | awk '{print $2}')
if [ ! -z "$VOLUME_NAME" ]; then
    CERT_DIR="/data/live/products.bunkov.in"
    if docker run --rm -v ${VOLUME_NAME}:/data alpine test -f $CERT_DIR/fullchain.pem 2>/dev/null; then
        echo "   ✅ Сертификат найден"
    else
        echo "   ❌ Сертификат не найден!"
    fi
else
    echo "   ❌ Volume certbot_data не найден"
fi

# 6. Проверяем конфигурацию nginx (детально)
echo ""
echo "6. Детальная проверка конфигурации nginx..."
if docker compose exec nginx nginx -t 2>&1 | grep -q "successful"; then
    echo "   ✅ Конфигурация nginx валидна"
else
    echo "   ❌ Ошибка в конфигурации nginx!"
    docker compose exec nginx nginx -t
fi

# 7. Проверяем логи nginx
echo ""
echo "7. Последние ошибки nginx..."
docker compose logs nginx | tail -10 | grep -i error || echo "   Нет ошибок в логах"

echo ""
echo "=========================================="
echo "Рекомендации:"
echo "=========================================="
echo ""
echo "Если порт 443 недоступен:"
echo "  1. Убедитесь, что применена полная конфигурация: ./apply-https.sh"
echo "  2. Проверьте, что nginx перезапущен: docker compose restart nginx"
echo "  3. Откройте порт 443 в firewall: sudo ufw allow 443/tcp"
echo "  4. Проверьте логи nginx: docker compose logs nginx | tail -20"
echo ""

