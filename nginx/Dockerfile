FROM nginx:alpine

# Удаляем стандартную конфигурацию
RUN rm /etc/nginx/conf.d/default.conf

# Копируем кастомную конфигурацию
COPY nginx.conf /etc/nginx/nginx.conf

# Создаем директорию для статических файлов
RUN mkdir -p /app/static

# Открываем порт 80
EXPOSE 80

# Проверяем конфигурацию nginx при запуске
CMD ["nginx", "-g", "daemon off;"]
