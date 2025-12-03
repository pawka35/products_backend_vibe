#!/usr/bin/env python3
"""
Скрипт для сброса пароля администратора
Использование: python3 reset_admin_password.py [новый_пароль]
Если пароль не указан, будет сгенерирован случайный
"""

import sys
import os
from database import SessionLocal
from auth.models.user_models import User, UserRole
from auth.utils.auth_utils import get_password_hash
from auth.utils.admin_init import generate_secure_password

# Импортируем все модели для правильной работы SQLAlchemy
import products.models  # noqa: F401
import notifications.models  # noqa: F401

def reset_admin_password(new_password: str = None):
    """
    Сбрасывает пароль администратора
    
    Args:
        new_password: Новый пароль (если не указан, генерируется случайный)
    
    Returns:
        tuple: (username, password) или (None, None) при ошибке
    """
    db = SessionLocal()
    try:
        # Находим администратора
        admin = db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.username == "admin"
        ).first()
        
        if not admin:
            print("❌ Администратор с username 'admin' не найден")
            return None, None
        
        # Генерируем или используем указанный пароль
        if new_password:
            password = new_password
        else:
            password = generate_secure_password(20)
        
        # Хешируем пароль
        try:
            hashed_password = get_password_hash(password)
        except Exception as e:
            print(f"❌ Ошибка хеширования пароля: {e}")
            return None, None
        
        # Обновляем пароль
        admin.hashed_password = hashed_password
        db.commit()
        db.refresh(admin)
        
        print("=" * 60)
        print("🔐 ПАРОЛЬ АДМИНИСТРАТОРА ОБНОВЛЕН")
        print("=" * 60)
        print(f"👤 Username: admin")
        print(f"📧 Email: {admin.email}")
        print(f"🔑 Password: {password}")
        print("=" * 60)
        print("⚠️  СОХРАНИТЕ ЭТОТ ПАРОЛЬ!")
        print("=" * 60)
        
        return "admin", password
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при сбросе пароля: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        db.close()

if __name__ == "__main__":
    # Получаем пароль из аргументов командной строки (если указан)
    new_password = sys.argv[1] if len(sys.argv) > 1 else None
    
    if new_password:
        print(f"Используется указанный пароль")
    else:
        print("Генерируется случайный пароль...")
    
    username, password = reset_admin_password(new_password)
    
    if username and password:
        print("\n✅ Пароль успешно обновлен!")
        sys.exit(0)
    else:
        print("\n❌ Не удалось обновить пароль")
        sys.exit(1)

