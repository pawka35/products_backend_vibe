# Система Telegram уведомлений

Система уведомлений через Telegram Bot API для отправки уведомлений о завершении заказов.

## Настройка

### 1. Создание Telegram бота

1. Откройте Telegram и найдите бота [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен (формат: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Настройка переменных окружения

Добавьте в `.env` файл:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ENABLED=true
```

### 3. Настройка webhook (опционально)

Для обработки команд бота (`/verify`, `/start`) нужно настроить webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/notifications/telegram/webhook"}'
```

Или используйте polling (не рекомендуется для продакшена).

### 4. Выполнение миграции

```bash
python migrations/add_telegram_notifications.py
```

## Использование

### Для пользователей

1. **Запросить код верификации:**
   - Войдите в систему
   - Перейдите в раздел уведомлений
   - Нажмите "Подключить Telegram"
   - Получите 6-значный код

2. **Привязать Telegram:**
   - Найдите вашего бота в Telegram
   - Отправьте команду: `/verify <код>`
   - Пример: `/verify 123456`

3. **Настроить уведомления:**
   - В разделе уведомлений можно включить/выключить:
     - Telegram уведомления (общее)
     - Уведомления о завершении заказов

### API Endpoints

#### Запросить код верификации
```
POST /notifications/telegram/request-code
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "code": "123456",
  "expires_in": 300,
  "message": "Отправьте боту @your_bot команду: /verify 123456"
}
```

#### Получить статус подключения
```
GET /notifications/telegram/status
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "connected": true,
  "telegram_id": 123456789
}
```

#### Отвязать Telegram
```
DELETE /notifications/telegram/disconnect
Authorization: Bearer <token>
```

#### Получить настройки уведомлений
```
GET /notifications/settings
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "telegram_enabled": true,
  "notify_order_completed": true
}
```

#### Обновить настройки уведомлений
```
PUT /notifications/settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "telegram_enabled": true,
  "notify_order_completed": false
}
```

## Автоматические уведомления

Система автоматически отправляет уведомления заказчику при завершении заказа (статус `COMPLETED`).

**Формат уведомления:**
```
✅ Заказ #123 завершен

Исполнитель: Иван Иванов
Дата завершения: 15.01.2024 14:30

Комментарий исполнителя:
Все продукты успешно приобретены.
```

## Условия отправки уведомлений

Уведомление отправляется только если:
1. Telegram уведомления включены в настройках пользователя
2. Уведомления о завершении заказа включены
3. У пользователя привязан Telegram ID
4. `TELEGRAM_ENABLED=true` в настройках приложения
5. Указан валидный `TELEGRAM_BOT_TOKEN`

## Обработка ошибок

- Если Telegram API недоступен, ошибка логируется, но не прерывает выполнение
- При ошибках отправки выполняется до 3 повторных попыток с экспоненциальной задержкой
- Все ошибки логируются в лог-файл

## Безопасность

- Коды верификации действительны 5 минут
- Коды одноразовые (после использования становятся недействительными)
- Telegram ID уникален (нельзя привязать один Telegram ID к нескольким аккаунтам)
- Webhook endpoint не требует аутентификации (но можно добавить проверку через `TELEGRAM_WEBHOOK_SECRET`)

