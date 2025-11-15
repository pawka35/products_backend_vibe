#!/bin/bash

# Скрипт для проверки и настройки Telegram webhook

set -e

echo "=========================================="
echo "🔍 Проверка Telegram Webhook"
echo "=========================================="
echo ""

# Проверяем наличие токена
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    if [ -f ".env" ]; then
        source .env
    fi
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не найден"
    echo "Добавьте в .env: TELEGRAM_BOT_TOKEN=your_token"
    exit 1
fi

echo "1. Проверка текущего webhook..."
CURRENT_WEBHOOK=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

if [ -z "$CURRENT_WEBHOOK" ]; then
    echo "   ⚠️  Webhook не настроен"
else
    echo "   ✅ Текущий webhook: $CURRENT_WEBHOOK"
fi

echo ""
echo "2. Проверка доступности webhook endpoint..."
DOMAIN="products.bunkov.in"
WEBHOOK_URL="https://${DOMAIN}/notifications/telegram/webhook"

# Проверяем доступность
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"message":{"chat":{"id":123},"text":"/start"}}' 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Webhook endpoint доступен (код: $HTTP_CODE)"
else
    echo "   ❌ Webhook endpoint недоступен (код: $HTTP_CODE)"
    echo "   Проверьте, что приложение запущено и доступно по адресу: $WEBHOOK_URL"
fi

echo ""
read -p "Настроить webhook на $WEBHOOK_URL? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "3. Настройка webhook..."
    RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"${WEBHOOK_URL}\"}")
    
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        echo "   ✅ Webhook успешно настроен!"
        echo "   URL: $WEBHOOK_URL"
    else
        echo "   ❌ Ошибка настройки webhook:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    fi
fi

echo ""
echo "4. Проверка информации о боте..."
BOT_INFO=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe")
if echo "$BOT_INFO" | grep -q '"ok":true'; then
    BOT_USERNAME=$(echo "$BOT_INFO" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    BOT_NAME=$(echo "$BOT_INFO" | grep -o '"first_name":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ Бот найден: @${BOT_USERNAME} ($BOT_NAME)"
else
    echo "   ❌ Ошибка получения информации о боте"
    echo "$BOT_INFO"
fi

echo ""
echo "=========================================="
echo "Проверка завершена"
echo "=========================================="
echo ""
echo "Для тестирования отправьте боту команду:"
echo "  /start"
echo "или"
echo "  /verify <код>"
echo ""

