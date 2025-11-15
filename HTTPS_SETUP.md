# Настройка HTTPS с Let's Encrypt (Certbot)

Это руководство поможет настроить HTTPS для домена `products.bunkov.in` с использованием Let's Encrypt и Certbot.

## Предварительные требования

1. **Домен должен указывать на IP сервера**
   - Убедитесь, что DNS запись для `products.bunkov.in` указывает на IP `195.234.208.160`
   - Проверьте: `nslookup products.bunkov.in` или `dig products.bunkov.in`

2. **Порты 80 и 443 должны быть открыты**
   - Проверьте, что порты 80 (HTTP) и 443 (HTTPS) открыты в firewall
   - Для проверки: `sudo ufw status` или `sudo iptables -L`

3. **Docker и Docker Compose установлены**
   - Проверьте: `docker --version` и `docker compose version`

## Шаги настройки

### 1. Обновите email в скрипте

Откройте файл `init-ssl.sh` и замените email на ваш:

```bash
EMAIL="admin@bunkov.in"  # Замените на ваш email
```

### 2. Запустите контейнеры (без HTTPS)

**Важно:** Перед первым запуском нужно использовать временную конфигурацию без HTTPS блока, так как сертификаты еще не получены.

```bash
# Сохраните текущую конфигурацию (с HTTPS)
cp nginx/nginx.conf nginx/nginx.conf.https

# Используйте временную конфигурацию для первого запуска
cp nginx/nginx.conf.template nginx/nginx.conf

# Запустите контейнеры
docker compose up -d
```

**Примечание:** После получения сертификата вы переключитесь на полную конфигурацию с HTTPS (см. шаг 5).

### 3. Проверьте доступность домена

Убедитесь, что домен доступен по HTTP:

```bash
curl http://products.bunkov.in/health
```

Должен вернуться ответ от FastAPI приложения.

### 4. Получите SSL сертификат

Запустите скрипт для получения сертификата:

```bash
./init-ssl.sh
```

Скрипт:
- Создаст необходимые директории
- Получит SSL сертификат от Let's Encrypt
- Перезагрузит Nginx

### 5. Примените полную конфигурацию HTTPS

После успешного получения сертификата, переключитесь на полную конфигурацию с редиректом HTTP→HTTPS:

```bash
# Переключитесь на полную конфигурацию с HTTPS
cp nginx/nginx.conf.https nginx/nginx.conf

# Пересоберите и перезапустите Nginx
docker compose build nginx
docker compose up -d nginx

# Проверьте конфигурацию
docker compose exec nginx nginx -t
```

Теперь все HTTP запросы будут автоматически редиректиться на HTTPS.

### 6. Проверьте HTTPS

Проверьте, что сайт доступен по HTTPS:

```bash
curl https://products.bunkov.in/health
```

Также проверьте редирект с HTTP на HTTPS:

```bash
curl -I http://products.bunkov.in
# Должен вернуть: HTTP/1.1 301 Moved Permanently
# Location: https://products.bunkov.in/...
```

## Автоматическое обновление сертификатов

Сертификаты Let's Encrypt действительны 90 дней. В `docker-compose.yml` настроен автоматический сервис `certbot`, который:
- Проверяет сертификаты каждые 12 часов
- Автоматически обновляет их при необходимости
- Перезагружает Nginx после обновления

Сервис `certbot` запускается автоматически вместе с остальными контейнерами.

## Проверка статуса сертификатов

Для проверки статуса сертификатов:

```bash
docker compose exec certbot certbot certificates
```

## Ручное обновление сертификатов

Если нужно обновить сертификаты вручную:

```bash
docker compose exec certbot certbot renew --force-renewal
docker compose exec nginx nginx -s reload
```

## Устранение проблем

### Ошибка: "Failed to obtain certificate"

**Причины:**
- Домен не указывает на IP сервера
- Порты 80/443 закрыты
- Nginx не может получить доступ к `/var/www/certbot`

**Решение:**
1. Проверьте DNS: `nslookup products.bunkov.in`
2. Проверьте firewall: `sudo ufw status`
3. Проверьте логи: `docker compose logs certbot`

### Ошибка: "nginx: [emerg] SSL certificate not found"

**Причина:** Сертификат еще не получен или путь к сертификату неверный.

**Решение:**
1. Убедитесь, что сертификат получен: `docker compose exec certbot certbot certificates`
2. Проверьте путь в `nginx.conf`: `/etc/letsencrypt/live/products.bunkov.in/`
3. Используйте временную конфигурацию `nginx.conf.template` до получения сертификата

### Nginx не перезагружается после получения сертификата

**Решение:**
```bash
docker compose exec nginx nginx -t  # Проверка конфигурации
docker compose exec nginx nginx -s reload  # Перезагрузка
```

## Безопасность

После настройки HTTPS убедитесь, что:

1. ✅ Все HTTP запросы редиректятся на HTTPS
2. ✅ Используются современные SSL протоколы (TLS 1.2+)
3. ✅ Включены security headers (HSTS, X-Frame-Options и т.д.)
4. ✅ Сертификаты автоматически обновляются

## Проверка безопасности SSL

Используйте онлайн инструменты для проверки:
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [Security Headers](https://securityheaders.com/)

## Дополнительная информация

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)

