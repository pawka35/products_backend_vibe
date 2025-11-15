# Устранение проблем с получением SSL сертификата

## Проблема: Скрипт зависает при получении сертификата

Если скрипт `init-ssl.sh` зависает на этапе получения сертификата, выполните следующие проверки:

### 1. Проверьте, что используется правильная конфигурация nginx

**ВАЖНО:** Перед получением сертификата должна использоваться временная конфигурация без HTTPS блока!

```bash
# Проверьте текущую конфигурацию
grep -q "# Временный прокси" nginx/nginx.conf && echo "✅ Используется временная конфигурация" || echo "❌ Нужна временная конфигурация"

# Если нужно, переключитесь на временную конфигурацию
cp nginx/nginx.conf.template nginx/nginx.conf
docker compose build nginx
docker compose up -d nginx
```

### 2. Проверьте доступность домена

```bash
# Проверьте DNS
nslookup products.bunkov.in
# Должен вернуть IP: 195.234.208.160

# Проверьте доступность по HTTP
curl -I http://products.bunkov.in
# Должен вернуть HTTP/1.1 200 OK или 301

# Проверьте ACME challenge endpoint
curl http://products.bunkov.in/.well-known/acme-challenge/test
# Должен вернуть 404 (это нормально, если файла нет)
```

### 3. Проверьте volumes в docker-compose

Убедитесь, что volume `certbot_www` правильно монтируется:

```bash
# Проверьте, что volume существует
docker volume ls | grep certbot_www

# Проверьте, что nginx видит директорию
docker compose exec nginx ls -la /var/www/certbot
# Должна быть директория (может быть пустой)

# Создайте тестовый файл
echo "test" | docker compose exec -T nginx tee /var/www/certbot/test.txt

# Проверьте доступность через HTTP
curl http://products.bunkov.in/.well-known/acme-challenge/test.txt
# Должен вернуть содержимое файла "test"
```

### 4. Проверьте логи

```bash
# Логи nginx
docker compose logs nginx | tail -50

# Логи certbot (если контейнер запущен)
docker compose logs certbot | tail -50
```

### 5. Запустите certbot вручную с подробным выводом

```bash
# Остановите сервис certbot
docker compose stop certbot

# Запустите certbot вручную с подробным выводом
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ваш-email@example.com \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --verbose \
    --dry-run \
    -d products.bunkov.in
```

Флаг `--dry-run` позволяет протестировать без реального получения сертификата.

### 6. Проверьте firewall и порты

```bash
# Проверьте, что порт 80 открыт
sudo netstat -tulpn | grep :80
# или
sudo ss -tulpn | grep :80

# Проверьте firewall
sudo ufw status
# Порты 80 и 443 должны быть открыты

# Если нужно, откройте порты
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 7. Проверьте, что nginx правильно настроен для ACME challenge

```bash
# Проверьте конфигурацию nginx
docker compose exec nginx nginx -t

# Проверьте, что location /.well-known/acme-challenge/ есть в конфигурации
docker compose exec nginx grep -A 3 "acme-challenge" /etc/nginx/nginx.conf
```

Должно быть:
```
location /.well-known/acme-challenge/ {
    root /var/www/certbot;
}
```

### 8. Альтернативный способ: использование standalone режима

Если webroot не работает, можно использовать standalone режим (требует остановки nginx):

```bash
# Остановите nginx
docker compose stop nginx

# Получите сертификат в standalone режиме
docker compose run --rm -p 80:80 certbot certonly \
    --standalone \
    --email ваш-email@example.com \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d products.bunkov.in

# Запустите nginx обратно
docker compose up -d nginx
```

### 9. Проверьте ограничения Let's Encrypt

Let's Encrypt имеет ограничения:
- Максимум 5 сертификатов на домен в неделю
- Максимум 50 поддоменов на домен в неделю

Если вы превысили лимит, нужно подождать или использовать `--force-renewal` (но это тоже ограничено).

### 10. Проверьте сетевую доступность

```bash
# Проверьте, что сервер доступен извне
# С другого компьютера или через онлайн сервис:
# https://www.yougetsignal.com/tools/open-ports/
# Проверьте порт 80 на IP 195.234.208.160
```

## Частые ошибки

### Ошибка: "Connection refused" или "Timeout"

**Причина:** Домен не указывает на IP сервера или порт 80 закрыт.

**Решение:**
1. Проверьте DNS: `nslookup products.bunkov.in`
2. Проверьте firewall: `sudo ufw status`
3. Проверьте, что nginx слушает на порту 80: `sudo netstat -tulpn | grep :80`

### Ошибка: "Failed to connect to Let's Encrypt"

**Причина:** Проблемы с сетью или firewall блокирует исходящие соединения.

**Решение:**
1. Проверьте исходящие соединения: `curl -I https://acme-v02.api.letsencrypt.org/directory`
2. Проверьте firewall для исходящих соединений

### Ошибка: "Invalid response from http://products.bunkov.in/.well-known/acme-challenge/..."

**Причина:** Nginx не может отдать файл из `/var/www/certbot`.

**Решение:**
1. Проверьте, что volume `certbot_www` монтируется в nginx
2. Проверьте права доступа: `docker compose exec nginx ls -la /var/www/certbot`
3. Проверьте конфигурацию nginx для location `/.well-known/acme-challenge/`

## Диагностика в реальном времени

Если скрипт зависает, откройте второй терминал и выполните:

```bash
# Следите за логами certbot в реальном времени
docker compose logs -f certbot

# Или следите за логами nginx
docker compose logs -f nginx

# Проверьте процессы
docker compose ps
```

## Если ничего не помогает

1. Убедитесь, что используете **временную конфигурацию** (`nginx.conf.template`)
2. Перезапустите все контейнеры: `docker compose down && docker compose up -d`
3. Попробуйте получить сертификат вручную (см. пункт 5)
4. Проверьте логи на наличие конкретных ошибок

