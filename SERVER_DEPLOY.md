# Инструкция по применению HTTPS на сервере

## Быстрая инструкция для сервера

### 1. Подключитесь к серверу

```bash
ssh user@195.234.208.160
# или
ssh user@products.bunkov.in
```

### 2. Перейдите в директорию проекта

```bash
cd /path/to/backend  # замените на путь к вашему проекту
```

### 3. Обновите код из репозитория

```bash
# Убедитесь, что вы на ветке main
git checkout main

# Получите последние изменения
git pull origin main
```

### 4. Проверьте DNS настройки

Убедитесь, что домен `products.bunkov.in` указывает на IP сервера `195.234.208.160`:

```bash
# Проверка DNS
nslookup products.bunkov.in
# или
dig products.bunkov.in

# Должен вернуть IP: 195.234.208.160
```

### 5. Проверьте открытые порты

Убедитесь, что порты 80 и 443 открыты:

```bash
# Проверка firewall (если используется ufw)
sudo ufw status

# Если порты закрыты, откройте их:
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

### 6. Подготовьте конфигурацию для первого запуска

**ВАЖНО:** Перед первым запуском нужно использовать временную конфигурацию без HTTPS блока:

```bash
# Сохраните текущую конфигурацию (с HTTPS) как резервную
cp nginx/nginx.conf nginx/nginx.conf.https

# Используйте временную конфигурацию для первого запуска
cp nginx/nginx.conf.template nginx/nginx.conf
```

### 7. Обновите email в скрипте получения сертификата

Откройте файл `init-ssl.sh` и замените email на ваш:

```bash
nano init-ssl.sh
# Найдите строку: EMAIL="admin@bunkov.in"
# Замените на ваш email
```

### 8. Остановите текущие контейнеры (если запущены)

```bash
docker compose down
```

### 9. Запустите контейнеры с временной конфигурацией

```bash
docker compose up -d
```

Проверьте, что все контейнеры запустились:

```bash
docker compose ps
```

Должны быть запущены:
- `fastapi_mysql` (Healthy)
- `fastapi_app` (Healthy)
- `fastapi_nginx` (Up)

### 10. Проверьте доступность домена по HTTP

```bash
curl http://products.bunkov.in/health
# или
curl http://195.234.208.160/health
```

Должен вернуться ответ от FastAPI приложения.

### 11. Получите SSL сертификат

```bash
# Убедитесь, что скрипт исполняемый
chmod +x init-ssl.sh

# Запустите скрипт получения сертификата
./init-ssl.sh
```

Скрипт:
- Остановит сервис certbot (если запущен), чтобы он не мешал
- Создаст необходимые директории
- Получит SSL сертификат от Let's Encrypt
- Запустит сервис certbot обратно для автоматического обновления
- Выведет инструкции по дальнейшим шагам

**Примечание:** Если возникнут ошибки, проверьте:
- DNS правильно настроен
- Порты 80/443 открыты
- Домен доступен извне
- Если скрипт зависает на "No renewals were attempted", это нормально - скрипт автоматически остановит сервис certbot перед получением сертификата

### 12. Примените полную конфигурацию HTTPS

После успешного получения сертификата:

```bash
# Переключитесь на полную конфигурацию с HTTPS
cp nginx/nginx.conf.https nginx/nginx.conf

# Пересоберите и перезапустите Nginx
docker compose build nginx
docker compose up -d nginx

# Проверьте конфигурацию Nginx
docker compose exec nginx nginx -t
```

Если проверка прошла успешно, перезагрузите Nginx:

```bash
docker compose exec nginx nginx -s reload
```

### 13. Проверьте HTTPS

```bash
# Проверьте доступность по HTTPS
curl https://products.bunkov.in/health

# Проверьте редирект с HTTP на HTTPS
curl -I http://products.bunkov.in
# Должен вернуть: HTTP/1.1 301 Moved Permanently
# Location: https://products.bunkov.in/...
```

### 14. Проверьте автоматическое обновление сертификатов

Сервис `certbot` должен автоматически запуститься и обновлять сертификаты:

```bash
# Проверьте статус certbot
docker compose ps certbot

# Проверьте список сертификатов
docker compose exec certbot certbot certificates
```

## Проверка работы

1. Откройте в браузере: `https://products.bunkov.in`
2. Проверьте, что HTTP редиректится на HTTPS
3. Проверьте SSL сертификат (должен быть валидный от Let's Encrypt)

## Устранение проблем

### Ошибка при получении сертификата

```bash
# Проверьте логи certbot
docker compose logs certbot

# Проверьте логи nginx
docker compose logs nginx

# Проверьте, что домен доступен
curl -I http://products.bunkov.in/.well-known/acme-challenge/test
```

### Nginx не запускается после применения HTTPS конфигурации

```bash
# Проверьте конфигурацию
docker compose exec nginx nginx -t

# Проверьте, что сертификаты существуют
docker compose exec nginx ls -la /etc/letsencrypt/live/products.bunkov.in/
```

### Порты заняты

```bash
# Проверьте, какие процессы используют порты 80 и 443
sudo netstat -tulpn | grep -E ':(80|443)'

# Если нужно, остановите другие сервисы
sudo systemctl stop apache2  # если установлен Apache
sudo systemctl stop nginx     # если установлен системный Nginx
```

## Дополнительная информация

Подробная документация находится в файле `HTTPS_SETUP.md`.

## После успешной настройки

После того, как HTTPS настроен и работает:

1. ✅ Все HTTP запросы автоматически редиректятся на HTTPS
2. ✅ Сертификаты автоматически обновляются каждые 12 часов
3. ✅ Nginx автоматически перезагружается после обновления сертификатов
4. ✅ Используются современные SSL протоколы и security headers

## Проверка безопасности SSL

Используйте онлайн инструменты:
- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/analyze.html?d=products.bunkov.in)
- [Security Headers](https://securityheaders.com/?q=https://products.bunkov.in)

