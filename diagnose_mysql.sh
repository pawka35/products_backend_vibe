#!/bin/bash

# Скрипт для диагностики проблем с MySQL контейнером
# Использование: ./diagnose_mysql.sh

echo "=========================================="
echo "Диагностика проблем с MySQL контейнером"
echo "=========================================="
echo ""

# 1. Проверка Docker
echo "1. Проверка Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi
echo "✅ Docker установлен: $(docker --version)"
echo ""

# 2. Проверка Docker Compose
echo "2. Проверка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi
echo "✅ Docker Compose установлен: $(docker-compose --version)"
echo ""

# 3. Проверка статуса контейнеров
echo "3. Статус контейнеров..."
docker-compose ps
echo ""

# 4. Проверка логов MySQL
echo "4. Последние логи MySQL контейнера..."
docker-compose logs mysql --tail=50
echo ""

# 5. Проверка занятости порта 3307
echo "5. Проверка порта 3307..."
if command -v netstat &> /dev/null; then
    netstat -tuln | grep 3307 || echo "Порт 3307 свободен"
elif command -v ss &> /dev/null; then
    ss -tuln | grep 3307 || echo "Порт 3307 свободен"
else
    echo "⚠️  Не удалось проверить порт (netstat/ss не установлены)"
fi
echo ""

# 6. Проверка Docker volumes
echo "6. Проверка Docker volumes..."
docker volume ls | grep mysql || echo "Volumes для MySQL не найдены"
echo ""

# 7. Проверка прав доступа
echo "7. Проверка прав доступа к директориям..."
ls -la | grep -E "logs|mysql_data" || echo "Директории не найдены"
echo ""

# 8. Проверка свободного места
echo "8. Проверка свободного места на диске..."
df -h
echo ""

# 9. Проверка памяти
echo "9. Проверка доступной памяти..."
free -h
echo ""

# 10. Попытка пересоздать контейнер
echo "10. Попытка пересоздать MySQL контейнер..."
read -p "Пересоздать MySQL контейнер? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Останавливаем контейнер..."
    docker-compose stop mysql
    echo "Удаляем контейнер..."
    docker-compose rm -f mysql
    echo "Удаляем volume (данные будут потеряны!)..."
    read -p "Удалить volume с данными MySQL? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume rm backend_mysql_data 2>/dev/null || echo "Volume не найден или уже удален"
    fi
    echo "Запускаем заново..."
    docker-compose up -d mysql
    echo "Ждем 10 секунд..."
    sleep 10
    echo "Проверяем статус..."
    docker-compose ps mysql
    echo "Логи:"
    docker-compose logs mysql --tail=20
fi

echo ""
echo "=========================================="
echo "Диагностика завершена"
echo "=========================================="

