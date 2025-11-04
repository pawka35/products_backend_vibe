"""
Миграция для добавления поля complete_comment в таблицу orders

Выполните этот скрипт для добавления колонки complete_comment в существующую базу данных:
    python migrations/add_complete_comment.py
"""

import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import engine, SessionLocal

def add_complete_comment_column():
    """Добавляет колонку complete_comment в таблицу orders"""
    
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли уже колонка
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='complete_comment'
        """)
        
        result = db.execute(check_query).fetchone()
        
        if result:
            print("✅ Колонка complete_comment уже существует в таблице orders")
            return
        
        # Добавляем колонку complete_comment
        alter_query = text("""
            ALTER TABLE orders 
            ADD COLUMN complete_comment TEXT NULL
        """)
        
        db.execute(alter_query)
        db.commit()
        
        print("✅ Колонка complete_comment успешно добавлена в таблицу orders")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при добавлении колонки: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Миграция: Добавление поля complete_comment в таблицу orders")
    print("=" * 60 + "\n")
    
    add_complete_comment_column()
    
    print("\n" + "=" * 60)
    print("Миграция завершена")
    print("=" * 60 + "\n")

