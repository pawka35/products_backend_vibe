#!/bin/bash

# Скрипт для проверки доступности домена извне

DOMAIN="products.bunkov.in"
IP="195.234.208.160"

echo "=========================================="
echo "Проверка доступности домена извне"
echo "=========================================="
echo ""

# 1. Проверка DNS
echo "1. Проверка DNS..."
DNS_IP=$(nslookup $DOMAIN 2>/dev/null | grep -A 1 "Name:" | tail -1 | awk '{print $2}')
if [ "$DNS_IP" = "$IP" ]; then
    echo "   ✅ DNS настроен правильно: $DOMAIN -> $IP"
else
    echo "   ❌ DNS настроен неправильно!"
    echo "   Ожидалось: $IP"
    echo "   Получено: $DNS_IP"
    echo "   Настройте DNS запись A для $DOMAIN на IP $IP"
fi

echo ""
echo "2. Проверка порта 80 на сервере..."
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    echo "   ✅ Порт 80 слушается на сервере"
    netstat -tuln | grep ":80 "
elif ss -tuln 2>/dev/null | grep -q ":80 "; then
    echo "   ✅ Порт 80 слушается на сервере (через ss)"
    ss -tuln | grep ":80 "
elif docker compose ps nginx | grep -q "Up"; then
    echo "   ⚠️  netstat не показывает порт 80 (это нормально для Docker)"
    echo "   Docker пробрасывает порты через iptables, а не напрямую"
    echo "   ✅ Nginx контейнер запущен - порт должен быть доступен"
else
    echo "   ❌ Порт 80 НЕ слушается и nginx не запущен!"
    echo "   Запустите: docker compose up -d nginx"
fi

echo ""
echo "3. Проверка firewall..."
if command -v ufw >/dev/null 2>&1; then
    echo "   Статус UFW:"
    sudo ufw status | head -10
    if sudo ufw status | grep -q "80/tcp.*ALLOW"; then
        echo "   ✅ Порт 80 открыт в firewall"
    else
        echo "   ⚠️  Порт 80 может быть закрыт в firewall"
        echo "   Откройте: sudo ufw allow 80/tcp"
    fi
elif command -v iptables >/dev/null 2>&1; then
    echo "   Проверка iptables:"
    sudo iptables -L -n | grep -E "80|ACCEPT" | head -5 || echo "   Не удалось проверить iptables"
else
    echo "   ⚠️  Firewall не найден (ufw или iptables)"
fi

echo ""
echo "4. Проверка nginx контейнера..."
if docker compose ps nginx | grep -q "Up"; then
    echo "   ✅ Nginx контейнер запущен"
    echo "   Проверка портов в контейнере:"
    docker compose exec nginx netstat -tuln 2>/dev/null | grep -E ":80|:443" || echo "   netstat недоступен в контейнере"
else
    echo "   ❌ Nginx контейнер не запущен!"
    echo "   Запустите: docker compose up -d nginx"
fi

echo ""
echo "5. Проверка доступности локально..."
LOCAL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/.well-known/acme-challenge/test 2>/dev/null)
if [ "$LOCAL_RESPONSE" = "404" ] || [ "$LOCAL_RESPONSE" = "403" ]; then
    echo "   ✅ Локально доступен (код: $LOCAL_RESPONSE - это нормально для несуществующего файла)"
else
    echo "   ⚠️  Локально недоступен (код: $LOCAL_RESPONSE)"
fi

echo ""
echo "6. Проверка доступности по IP..."
IP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$IP/.well-known/acme-challenge/test 2>/dev/null)
if [ "$IP_RESPONSE" = "404" ] || [ "$IP_RESPONSE" = "403" ]; then
    echo "   ✅ По IP доступен (код: $IP_RESPONSE - это нормально для несуществующего файла)"
else
    echo "   ❌ По IP недоступен (код: $IP_RESPONSE)"
    echo "   Это может означать, что порт 80 закрыт извне"
fi

echo ""
echo "7. Проверка доступности по домену..."
DOMAIN_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/.well-known/acme-challenge/test 2>/dev/null)
if [ "$DOMAIN_RESPONSE" = "404" ] || [ "$DOMAIN_RESPONSE" = "403" ]; then
    echo "   ✅ По домену доступен (код: $DOMAIN_RESPONSE - это нормально для несуществующего файла)"
else
    echo "   ❌ По домену недоступен (код: $DOMAIN_RESPONSE)"
fi

echo ""
echo "=========================================="
echo "Рекомендации:"
echo "=========================================="
echo ""
if [ "$IP_RESPONSE" != "404" ] && [ "$IP_RESPONSE" != "403" ]; then
    echo "⚠️  Проблема: Домен недоступен извне"
    echo ""
    echo "Возможные решения:"
    echo "1. Откройте порт 80 в firewall:"
    echo "   sudo ufw allow 80/tcp"
    echo "   sudo ufw reload"
    echo ""
    echo "2. Проверьте настройки провайдера/хостинга:"
    echo "   - Убедитесь, что порт 80 не заблокирован на уровне провайдера"
    echo "   - Проверьте настройки безопасности в панели управления"
    echo ""
    echo "3. Проверьте, что nginx слушает на всех интерфейсах (0.0.0.0):"
    echo "   docker compose exec nginx netstat -tuln | grep :80"
    echo ""
    echo "4. Используйте онлайн-сервисы для проверки:"
    echo "   https://www.yougetsignal.com/tools/open-ports/"
    echo "   Проверьте порт 80 на IP $IP"
fi

echo ""
echo "=========================================="
echo "Проверка завершена"
echo "=========================================="

