"""
Миграция для изменения типа колонки telegram_id с INT на BIGINT.
Telegram ID может быть больше максимального значения INT (2,147,483,647).
"""

import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import SessionLocal


def fix_telegram_id_bigint():
    """Изменяет тип колонки telegram_id с INT на BIGINT в таблицах users и telegram_verification_codes"""
    
    db = SessionLocal()
    try:
        with db.begin():
            # 1. Исправляем telegram_id в таблице users
            print("1. Проверяем текущий тип колонки 'telegram_id' в таблице 'users'...")
            result = db.execute(text("""
                SELECT DATA_TYPE 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'users' 
                AND column_name = 'telegram_id'
            """)).scalar()
            
            if result is None:
                print("   ⚠️  Колонка 'telegram_id' не найдена в таблице 'users'. Возможно, миграция add_telegram_notifications еще не применена.")
            elif result.upper() == 'BIGINT':
                print("   ✅ Колонка 'telegram_id' в таблице 'users' уже имеет тип BIGINT.")
            elif result.upper() == 'INT':
                print("   Изменяем тип колонки 'telegram_id' с INT на BIGINT в таблице 'users'...")
                db.execute(text("ALTER TABLE users MODIFY COLUMN telegram_id BIGINT NULL"))
                print("   ✅ Колонка 'telegram_id' в таблице 'users' успешно изменена на BIGINT.")
            else:
                print(f"   ⚠️  Неожиданный тип колонки в таблице 'users': {result}. Ожидался INT или BIGINT.")
            
            # 2. Исправляем telegram_id в таблице telegram_verification_codes
            print("\n2. Проверяем текущий тип колонки 'telegram_id' в таблице 'telegram_verification_codes'...")
            result = db.execute(text("""
                SELECT DATA_TYPE 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() 
                AND table_name = 'telegram_verification_codes' 
                AND column_name = 'telegram_id'
            """)).scalar()
            
            if result is None:
                print("   ⚠️  Колонка 'telegram_id' не найдена в таблице 'telegram_verification_codes'. Возможно, миграция add_telegram_notifications еще не применена.")
            elif result.upper() == 'BIGINT':
                print("   ✅ Колонка 'telegram_id' в таблице 'telegram_verification_codes' уже имеет тип BIGINT.")
            elif result.upper() == 'INT':
                print("   Изменяем тип колонки 'telegram_id' с INT на BIGINT в таблице 'telegram_verification_codes'...")
                db.execute(text("ALTER TABLE telegram_verification_codes MODIFY COLUMN telegram_id BIGINT NULL"))
                print("   ✅ Колонка 'telegram_id' в таблице 'telegram_verification_codes' успешно изменена на BIGINT.")
            else:
                print(f"   ⚠️  Неожиданный тип колонки в таблице 'telegram_verification_codes': {result}. Ожидался INT или BIGINT.")
        
        db.commit()
        print("\n✅ Миграция успешно завершена!")
        return True
                
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
    print("Миграция: Изменение типа telegram_id на BIGINT")
    print("=" * 60)
    fix_telegram_id_bigint()
    print("=" * 60)
