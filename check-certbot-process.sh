#!/bin/bash

# Скрипт для проверки процесса certbot

echo "=========================================="
echo "Проверка процесса certbot"
echo "=========================================="
echo ""

# 1. Проверяем запущенные контейнеры certbot
echo "1. Проверка запущенных контейнеров certbot..."
docker ps | grep certbot || echo "   Нет запущенных контейнеров certbot"

echo ""
echo "2. Проверка процессов certbot..."
ps aux | grep certbot | grep -v grep || echo "   Нет процессов certbot"

echo ""
echo "3. Проверка лог-файла..."
if [ -f /tmp/certbot-output.log ]; then
    echo "   ✅ Лог-файл существует: /tmp/certbot-output.log"
    echo "   Размер: $(wc -l < /tmp/certbot-output.log) строк"
    echo "   Последние 20 строк:"
    tail -20 /tmp/certbot-output.log | sed 's/^/   /'
else
    echo "   ❌ Лог-файл не существует: /tmp/certbot-output.log"
    echo "   Certbot еще не запустился или скрипт не начал выполнение"
fi

echo ""
echo "4. Проверка docker compose процессов..."
docker compose ps | grep -E "certbot|nginx"

echo ""
echo "5. Проверка последних логов certbot контейнера..."
if docker ps | grep -q certbot; then
    echo "   Логи запущенного контейнера:"
    docker logs $(docker ps | grep certbot | awk '{print $1}') --tail 20 2>&1 | sed 's/^/   /'
else
    echo "   Нет запущенных контейнеров certbot"
fi

echo ""
echo "6. Проверка процессов init-ssl.sh..."
if pgrep -f "init-ssl.sh" > /dev/null; then
    echo "   ✅ Скрипт init-ssl.sh запущен (PID: $(pgrep -f init-ssl.sh))"
else
    echo "   ❌ Скрипт init-ssl.sh не запущен"
fi

echo ""
echo "=========================================="
echo "Рекомендации:"
echo "=========================================="
echo ""
echo "Если certbot не запустился:"
echo "  1. Проверьте, что скрипт init-ssl.sh все еще выполняется"
echo "  2. Проверьте вывод скрипта в первом терминале"
echo "  3. Попробуйте запустить certbot вручную:"
echo "     docker compose run --rm certbot certonly \\"
echo "       --webroot \\"
echo "       --webroot-path=/var/www/certbot \\"
echo "       --email admin@bunkov.in \\"
echo "       --agree-tos \\"
echo "       --no-eff-email \\"
echo "       --non-interactive \\"
echo "       --verbose \\"
echo "       -d products.bunkov.in"
echo ""

