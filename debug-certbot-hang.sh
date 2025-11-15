#!/bin/bash

# Скрипт для диагностики зависания certbot

echo "=========================================="
echo "Диагностика зависания certbot"
echo "=========================================="
echo ""

# 1. Проверяем запущенные контейнеры
echo "1. Проверка запущенных контейнеров certbot..."
docker ps -a | grep certbot

echo ""
echo "2. Проверка процессов docker compose..."
ps aux | grep "docker compose run" | grep certbot | grep -v grep

echo ""
echo "3. Проверка сети Docker..."
docker network ls | grep app_network

echo ""
echo "4. Попытка запуска простого контейнера certbot (тест)..."
echo "   Запускаем: docker compose run --rm certbot echo 'test'"
timeout 10 docker compose run --rm certbot echo 'test' 2>&1 || echo "   ⚠️  Контейнер зависает или превысил таймаут"

echo ""
echo "5. Проверка образа certbot..."
docker images | grep certbot

echo ""
echo "6. Проверка volumes..."
docker volume ls | grep certbot

echo ""
echo "7. Попытка запуска certbot с минимальными параметрами..."
echo "   Запускаем: docker compose run --rm certbot --version"
timeout 10 docker compose run --rm certbot --version 2>&1 || echo "   ⚠️  Контейнер зависает или превысил таймаут"

echo ""
echo "=========================================="
echo "Рекомендации:"
echo "=========================================="
echo ""
echo "Если контейнер зависает даже на простых командах:"
echo "  1. Проверьте, не блокирует ли firewall исходящие соединения"
echo "  2. Проверьте DNS: docker compose run --rm certbot nslookup products.bunkov.in"
echo "  3. Попробуйте пересоздать сеть: docker compose down && docker compose up -d"
echo "  4. Проверьте логи Docker: journalctl -u docker -n 50"
echo ""

