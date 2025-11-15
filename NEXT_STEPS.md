# Следующие шаги после настройки HTTPS

## Текущая ситуация

✅ ACME challenge endpoint работает правильно
✅ Файлы успешно создаются и читаются через HTTP
✅ Конфигурация nginx настроена корректно

## Шаг 1: Проверьте, получен ли сертификат

```bash
# Обновите код на сервере
git pull origin main

# Проверьте наличие сертификатов
./check-certificates.sh

# Или проверьте напрямую
docker compose run --rm certbot certbot certificates
```

## Шаг 2A: Если сертификат УЖЕ получен

Если сертификат уже есть, примените полную конфигурацию HTTPS:

```bash
# 1. Переключитесь на полную конфигурацию с HTTPS
cp nginx/nginx.conf.https nginx/nginx.conf

# 2. Пересоберите и перезапустите nginx
docker compose build nginx
docker compose restart nginx

# 3. Проверьте конфигурацию nginx
docker compose exec nginx nginx -t

# 4. Проверьте HTTPS
curl https://products.bunkov.in/health

# 5. Проверьте редирект HTTP -> HTTPS
curl -I http://products.bunkov.in
# Должен вернуть: HTTP/1.1 301 Moved Permanently
# Location: https://products.bunkov.in/...
```

## Шаг 2B: Если сертификат НЕ получен

Если сертификат еще не получен, запустите получение:

```bash
# Запустите скрипт получения сертификата
./init-ssl.sh
```

**Время ожидания:** Обычно 1-3 минуты. Если зависает дольше 5 минут:
- Прервите процесс (Ctrl+C)
- Проверьте логи: `docker compose logs certbot | tail -50`
- Проверьте доступность домена извне

## Шаг 3: После успешного получения сертификата

После того, как сертификат получен:

1. **Примените полную конфигурацию HTTPS** (см. Шаг 2A)

2. **Запустите сервис certbot для автоматического обновления:**
```bash
docker compose up -d certbot
```

3. **Проверьте работу HTTPS:**
```bash
# Проверьте HTTPS
curl https://products.bunkov.in/health

# Проверьте в браузере
# Откройте: https://products.bunkov.in
```

4. **Проверьте автоматическое обновление сертификатов:**
```bash
# Проверьте статус certbot
docker compose ps certbot

# Проверьте список сертификатов
docker compose run --rm certbot certbot certificates
```

## Шаг 4: Проверка безопасности SSL

Используйте онлайн инструменты для проверки:
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/analyze.html?d=products.bunkov.in)
- [Security Headers](https://securityheaders.com/?q=https://products.bunkov.in)

## Устранение проблем

### Проблема: Сертификат не получен

1. Проверьте логи certbot:
```bash
docker compose logs certbot | tail -50
```

2. Проверьте доступность домена извне:
```bash
# С другого компьютера или через онлайн сервис
curl http://products.bunkov.in/.well-known/acme-challenge/test
```

3. Проверьте DNS:
```bash
nslookup products.bunkov.in
# Должен вернуть: 195.234.208.160
```

4. Проверьте порты:
```bash
sudo netstat -tulpn | grep -E ':(80|443)'
```

### Проблема: Nginx не запускается после применения HTTPS конфигурации

1. Проверьте конфигурацию:
```bash
docker compose exec nginx nginx -t
```

2. Проверьте наличие сертификатов:
```bash
docker compose run --rm certbot ls -la /etc/letsencrypt/live/products.bunkov.in/
```

3. Если сертификаты есть, но nginx не запускается, проверьте пути в конфигурации

## Финальная проверка

После настройки HTTPS убедитесь, что:

- ✅ Сайт доступен по HTTPS: `https://products.bunkov.in`
- ✅ HTTP автоматически редиректится на HTTPS
- ✅ SSL сертификат валидный (зеленый замочек в браузере)
- ✅ Сервис certbot запущен для автоматического обновления
- ✅ Security headers работают

## Дополнительная информация

- Подробная документация: `HTTPS_SETUP.md`
- Устранение проблем: `TROUBLESHOOT_SSL.md`
- Инструкции по развертыванию: `SERVER_DEPLOY.md`

