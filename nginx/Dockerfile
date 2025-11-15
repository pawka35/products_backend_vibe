FROM nginx:alpine

# Удаляем стандартную конфигурацию
RUN rm /etc/nginx/conf.d/default.conf

# Копируем кастомную конфигурацию
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем директорию для статических файлов
RUN mkdir -p /app/static

# Открываем порты 80 (HTTP) и 443 (HTTPS)
EXPOSE 80 443

# Проверяем конфигурацию nginx при запуске
CMD ["nginx", "-g", "daemon off;"]
