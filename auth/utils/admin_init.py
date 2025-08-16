import secrets
import string
from sqlalchemy.orm import Session
from auth.models.user_models import User, UserRole
from auth.utils.auth_utils import get_password_hash
from database import get_db

def generate_secure_password(length: int = 16) -> str:
    """Генерирует безопасный пароль"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_initial_admin(db: Session) -> tuple[str, str]:
    """
    Создает первого администратора, если его нет в базе
    Возвращает кортеж (username, password)
    """
    # Проверяем, есть ли уже администратор
    existing_admin = db.query(User).filter(
        User.role == UserRole.ADMIN
    ).first()
    
    if existing_admin:
        return None, None  # Администратор уже существует
    
    # Генерируем безопасный пароль
    password = generate_secure_password(20)
    hashed_password = get_password_hash(password)
    
    # Создаем администратора
    admin_user = User(
        username="admin",
        email="admin@system.local",
        hashed_password=hashed_password,
        role=UserRole.ADMIN,
        is_active=True
    )
    
    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("=" * 60)
        print("🔐 СОЗДАН ПЕРВЫЙ АДМИНИСТРАТОР")
        print("=" * 60)
        print(f"👤 Username: admin")
        print(f"🔑 Password: {password}")
        print(f"📧 Email: admin@system.local")
        print("=" * 60)
        print("⚠️  СОХРАНИТЕ ЭТОТ ПАРОЛЬ! Он больше не будет показан!")
        print("=" * 60)
        
        return "admin", password
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка создания администратора: {e}")
        return None, None

def ensure_admin_exists():
    """Проверяет и создает администратора при необходимости"""
    try:
        db = next(get_db())
        username, password = create_initial_admin(db)
        
        if username and password:
            return True
        else:
            print("✅ Администратор уже существует в системе")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки администратора: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
