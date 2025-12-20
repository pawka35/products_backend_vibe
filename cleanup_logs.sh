#!/bin/bash
# Скрипт для очистки старых логов
# Использование: ./cleanup_logs.sh [дней] (по умолчанию 7 дней)

set -e

DAYS_TO_KEEP=${1:-7}  # По умолчанию храним логи за 7 дней
LOGS_DIR="./logs"
NGINX_LOGS_DIR="./nginx/logs"

echo "=========================================="
echo "🧹 Очистка старых логов"
echo "=========================================="
echo "Храним логи за последние $DAYS_TO_KEEP дней"
echo ""

# Функция для очистки логов в директории
cleanup_logs() {
    local dir=$1
    local name=$2
    
    if [ ! -d "$dir" ]; then
        echo "⚠️  Директория $dir не существует, пропускаем"
        return
    fi
    
    echo "📁 Очистка $name ($dir)..."
    
    # Находим и удаляем файлы старше указанного количества дней
    find "$dir" -type f -name "*.log" -mtime +$DAYS_TO_KEEP -delete 2>/dev/null || true
    
    # Также удаляем старые ротированные логи
    find "$dir" -type f -name "*.log.*" -mtime +$DAYS_TO_KEEP -delete 2>/dev/null || true
    
    # Показываем размер после очистки
    if [ -d "$dir" ]; then
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "0")
        echo "   ✅ Размер после очистки: $SIZE"
    fi
}

# Очищаем логи приложения
cleanup_logs "$LOGS_DIR" "логи приложения"

# Очищаем логи nginx
cleanup_logs "$NGINX_LOGS_DIR" "логи nginx"

echo ""
echo "=========================================="
echo "✅ Очистка завершена"
echo "=========================================="
echo ""
echo "Текущее использование диска:"
df -h . | tail -1

