"""
Автоматическое применение миграций
Проверяет, какие миграции нужно применить, и применяет их
"""

import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import SessionLocal

def check_migration_needed(db, check_query, description):
    """
    Проверяет, нужно ли применять миграцию
    
    Args:
        db: Сессия базы данных
        check_query: SQL запрос для проверки (должен вернуть 0 если нужно применить)
        description: Описание того, что проверяется
        
    Returns:
        True если миграция нужна, False если уже применена
    """
    try:
        result = db.execute(text(check_query)).scalar()
        return result == 0
    except Exception as e:
        # Если таблица не существует, значит миграция нужна
        return True

def apply_migrations():
    """Применяет все необходимые миграции"""
    
    db = SessionLocal()
    migrations_applied = []
    
    try:
        # Миграция 1: add_complete_comment
        print("Проверка миграции: add_complete_comment...")
        check_query = """
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_schema = DATABASE() AND table_name = 'orders' 
            AND column_name = 'complete_comment'
        """
        
        if check_migration_needed(db, check_query, "колонка complete_comment"):
            print("   Применяем миграцию add_complete_comment...")
            # Закрываем текущую сессию перед применением миграции
            db.close()
            from migrations.add_complete_comment import add_complete_comment_column
            add_complete_comment_column()
            migrations_applied.append("add_complete_comment")
            # Создаем новую сессию для следующих проверок
            db = SessionLocal()
            print("   ✅ Миграция add_complete_comment применена")
        else:
            print("   ✅ Миграция add_complete_comment уже применена")
        
        # Миграция 2: add_telegram_notifications
        print("\nПроверка миграции: add_telegram_notifications...")
        
        # Проверяем несколько условий
        check_telegram_id = """
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_schema = DATABASE() AND table_name = 'users' 
            AND column_name = 'telegram_id'
        """
        
        check_notification_settings = """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = 'notification_settings'
        """
        
        check_verification_codes = """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = 'telegram_verification_codes'
        """
        
        needs_migration = (
            check_migration_needed(db, check_telegram_id, "колонка telegram_id") or
            check_migration_needed(db, check_notification_settings, "таблица notification_settings") or
            check_migration_needed(db, check_verification_codes, "таблица telegram_verification_codes")
        )
        
        if needs_migration:
            print("   Применяем миграцию add_telegram_notifications...")
            # Закрываем текущую сессию перед применением миграции
            db.close()
            from migrations.add_telegram_notifications import add_telegram_notifications
            add_telegram_notifications()
            migrations_applied.append("add_telegram_notifications")
            print("   ✅ Миграция add_telegram_notifications применена")
        else:
            print("   ✅ Миграция add_telegram_notifications уже применена")
        
        # Миграция 3: fix_telegram_id_bigint
        print("\nПроверка миграции: fix_telegram_id_bigint...")
        check_telegram_id_type = """
            SELECT DATA_TYPE 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'users' 
            AND column_name = 'telegram_id'
        """
        
        try:
            telegram_id_type = db.execute(text(check_telegram_id_type)).scalar()
            if telegram_id_type and telegram_id_type.upper() == 'INT':
                print("   Применяем миграцию fix_telegram_id_bigint...")
                # Закрываем текущую сессию перед применением миграции
                db.close()
                from migrations.fix_telegram_id_bigint import fix_telegram_id_bigint
                fix_telegram_id_bigint()
                migrations_applied.append("fix_telegram_id_bigint")
                # Создаем новую сессию для следующих проверок
                db = SessionLocal()
                print("   ✅ Миграция fix_telegram_id_bigint применена")
            elif telegram_id_type and telegram_id_type.upper() == 'BIGINT':
                print("   ✅ Миграция fix_telegram_id_bigint уже применена (тип BIGINT)")
            elif telegram_id_type is None:
                print("   ⚠️  Колонка telegram_id не найдена, пропускаем миграцию fix_telegram_id_bigint")
            else:
                print(f"   ⚠️  Неожиданный тип колонки telegram_id: {telegram_id_type}")
        except Exception as e:
            print(f"   ⚠️  Ошибка при проверке типа колонки telegram_id: {e}")
        
        if migrations_applied:
            print(f"\n✅ Применено миграций: {len(migrations_applied)}")
            for migration in migrations_applied:
                print(f"   - {migration}")
        else:
            print("\n✅ Все миграции уже применены")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при применении миграций: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            db.close()
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("Проверка и применение миграций")
    print("=" * 60)
    print("")
    apply_migrations()
    print("")
    print("=" * 60)

