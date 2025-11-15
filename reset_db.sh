#!/bin/bash

# Скрипт для пересоздания локальной БД и создания нового админа
# Использование: ./reset_db.sh

set -e

echo "=========================================="
echo "🗑️  Пересоздание базы данных"
echo "=========================================="
echo ""
echo "⚠️  ВНИМАНИЕ: Все данные в базе будут удалены!"
read -p "Продолжить? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено"
    exit 1
fi

echo ""
echo "1. Останавливаем контейнеры..."
docker compose down
echo "   ✅ Контейнеры остановлены"
echo ""

echo "2. Удаляем volume с данными БД..."
docker volume rm products_backend_vibe_mysql_data 2>/dev/null || {
    # Пробуем найти volume по другому имени
    VOLUME_NAME=$(docker volume ls | grep mysql_data | awk '{print $2}' | head -1)
    if [ ! -z "$VOLUME_NAME" ]; then
        echo "   Найден volume: $VOLUME_NAME"
        docker volume rm $VOLUME_NAME
    else
        echo "   ⚠️  Volume не найден (возможно, уже удален)"
    fi
}
echo "   ✅ Volume удален"
echo ""

echo "3. Запускаем контейнеры заново..."
docker compose up -d mysql
echo "   ✅ MySQL контейнер запущен"
echo ""

echo "4. Ждем готовности БД..."
sleep 10
echo "   ✅ БД готова"
echo ""

echo "5. Создаем таблицы в БД..."
# Активируем venv если есть
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Создаем все таблицы через SQLAlchemy
python3 << 'EOF'
# Импортируем все модули, чтобы модели зарегистрировались в Base.metadata
import auth.models
import products.models
import notifications.models

from database import engine, Base, SessionLocal
from auth.utils.init_roles import ensure_basic_roles as ensure_role_models

print("   Создаем таблицы...")
Base.metadata.create_all(bind=engine)
print("   ✅ Таблицы созданы")

# Инициализируем базовые роли
print("   Инициализируем базовые роли...")
db = SessionLocal()
try:
    ensure_role_models(db)
    db.commit()
    print("   ✅ Базовые роли инициализированы")
except Exception as e:
    print(f"   ⚠️  Ошибка при инициализации ролей: {e}")
    db.rollback()
finally:
    db.close()
EOF
echo ""

echo "6. Выполняем миграции..."
# Выполняем миграцию для Telegram уведомлений
if [ -f "migrations/add_telegram_notifications.py" ]; then
    python3 migrations/add_telegram_notifications.py
    echo "   ✅ Миграция add_telegram_notifications выполнена"
fi
echo ""

echo "7. Создаем нового админа..."
# Запускаем Python скрипт для создания админа
python3 << 'EOF'
# Импортируем все модели перед использованием
import auth.models
import products.models
import notifications.models

from database import SessionLocal
from auth.utils.admin_init import create_initial_admin

db = SessionLocal()
try:
    username, password = create_initial_admin(db)
    if username and password:
        print(f"   ✅ Администратор создан!")
        print(f"   👤 Username: {username}")
        print(f"   🔑 Password: {password}")
        print(f"   ⚠️  СОХРАНИТЕ ПАРОЛЬ!")
    else:
        print("   ⚠️  Администратор уже существует")
finally:
    db.close()
EOF

echo ""
echo "=========================================="
echo "✅ База данных пересоздана!"
echo "=========================================="
echo ""
echo "Теперь можно запустить приложение:"
echo "  ./run_local.sh"
echo "  или"
echo "  docker compose up -d"
echo ""

