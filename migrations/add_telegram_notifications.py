"""
Миграция для добавления поддержки Telegram уведомлений

Выполните этот скрипт для добавления:
1. Колонки telegram_id в таблицу users
2. Таблицы notification_settings
3. Таблицы telegram_verification_codes

Выполнение:
    python migrations/add_telegram_notifications.py
"""

import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, SessionLocal
from datetime import datetime, timedelta

def add_telegram_notifications():
    """Добавляет поддержку Telegram уведомлений"""
    
    db = SessionLocal()
    try:
        with db.begin():
            # 1. Добавляем колонку telegram_id в таблицу users
            print("1. Проверяем наличие колонки 'telegram_id' в таблице 'users'...")
            result = db.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = 'users' "
                "AND column_name = 'telegram_id'"
            )).scalar()
            
            if result == 0:
                print("   Добавляем колонку 'telegram_id' в таблицу 'users'...")
                db.execute(text(
                    "ALTER TABLE users ADD COLUMN telegram_id BIGINT NULL UNIQUE, "
                    "ADD INDEX idx_users_telegram_id (telegram_id)"
                ))
                print("   ✅ Колонка 'telegram_id' успешно добавлена (тип BIGINT).")
            else:
                print("   ✅ Колонка 'telegram_id' уже существует в таблице 'users'.")
            
            # 2. Создаем таблицу notification_settings
            print("\n2. Проверяем наличие таблицы 'notification_settings'...")
            result = db.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = 'notification_settings'"
            )).scalar()
            
            if result == 0:
                print("   Создаем таблицу 'notification_settings'...")
                db.execute(text("""
                    CREATE TABLE notification_settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL UNIQUE,
                        telegram_enabled BOOLEAN DEFAULT TRUE,
                        notify_order_completed BOOLEAN DEFAULT TRUE,
                        created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                        updated_at DATETIME(6) NULL ON UPDATE CURRENT_TIMESTAMP(6),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_notification_settings_user_id (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                print("   ✅ Таблица 'notification_settings' успешно создана.")
            else:
                print("   ✅ Таблица 'notification_settings' уже существует.")
            
            # 3. Создаем таблицу telegram_verification_codes
            print("\n3. Проверяем наличие таблицы 'telegram_verification_codes'...")
            result = db.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = DATABASE() AND table_name = 'telegram_verification_codes'"
            )).scalar()
            
            if result == 0:
                print("   Создаем таблицу 'telegram_verification_codes'...")
                db.execute(text("""
                    CREATE TABLE telegram_verification_codes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        code VARCHAR(6) NOT NULL,
                        telegram_id BIGINT NULL,
                        expires_at DATETIME(6) NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_telegram_verification_codes_user_id (user_id),
                        INDEX idx_telegram_verification_codes_code (code),
                        INDEX idx_telegram_verification_codes_used (used)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                print("   ✅ Таблица 'telegram_verification_codes' успешно создана.")
            else:
                print("   ✅ Таблица 'telegram_verification_codes' уже существует.")
            
            # 4. Создаем записи настроек уведомлений для существующих пользователей
            print("\n4. Создаем настройки уведомлений для существующих пользователей...")
            db.execute(text("""
                INSERT IGNORE INTO notification_settings (user_id, telegram_enabled, notify_order_completed)
                SELECT id, TRUE, TRUE
                FROM users
                WHERE id NOT IN (SELECT user_id FROM notification_settings)
            """))
            created_count = db.execute(text("SELECT ROW_COUNT()")).scalar()
            if created_count > 0:
                print(f"   ✅ Создано {created_count} записей настроек уведомлений.")
            else:
                print("   ✅ Все пользователи уже имеют настройки уведомлений.")
            
        db.commit()
        print("\n✅ Миграция успешно завершена!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка при выполнении миграции: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Миграция: Добавление поддержки Telegram уведомлений")
    print("=" * 60)
    add_telegram_notifications()
    print("=" * 60)

