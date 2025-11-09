import secrets
import string
from sqlalchemy.orm import Session
from auth.models.user_models import User, UserRole
from auth.utils.auth_utils import get_password_hash
from database import get_db
from auth.models.role_models import Role

def generate_secure_password(length: int = 16) -> str:
    """
    Генерирует безопасный пароль.
    Bcrypt имеет ограничение на длину пароля - максимум 72 байта.
    Для безопасности используем длину не более 70 символов (ASCII).
    """
    # Ограничиваем длину до 70 символов для безопасности (bcrypt ограничение - 72 байта)
    if length > 70:
        length = 70
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Дополнительная проверка: убеждаемся, что пароль не превышает 72 байта
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Обрезаем до 72 байт
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
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
    
    # Генерируем безопасный пароль (максимум 70 символов из-за ограничения bcrypt)
    password = generate_secure_password(20)
    
    # Дополнительная проверка длины пароля перед хешированием
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        print(f"⚠️  Предупреждение: пароль слишком длинный ({len(password_bytes)} байт), обрезаем до 72 байт")
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    
    try:
        hashed_password = get_password_hash(password)
    except Exception as e:
        print(f"❌ Ошибка хеширования пароля: {e}")
        # Пробуем с более коротким паролем
        password = generate_secure_password(16)
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

def create_basic_roles(db: Session) -> bool:
    """
    Создает базовые роли в системе, если их нет
    """
    try:
        # Проверяем, есть ли уже роли
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            print("✅ Базовые роли уже существуют в системе")
            return True
        
        # Создаем базовые роли
        basic_roles = [
            {
                "name": "admin",
                "description": "Системная роль администратора",
                "permissions": '{"all": true}',
                "is_active": True
            },
            {
                "name": "customer",
                "description": "Роль покупателя",
                "permissions": '{"read_products": true, "create_orders": true}',
                "is_active": True
            },
            {
                "name": "executor",
                "description": "Роль исполнителя заказов",
                "permissions": '{"read_orders": true, "update_orders": true}',
                "is_active": True
            }
        ]
        
        for role_data in basic_roles:
            role = Role(**role_data)
            db.add(role)
        
        db.commit()
        print("✅ Созданы базовые роли: admin, customer, executor")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка создания базовых ролей: {e}")
        return False

def ensure_basic_roles():
    """Проверяет и создает базовые роли при необходимости"""
    try:
        db = next(get_db())
        success = create_basic_roles(db)
        return success
        
    except Exception as e:
        print(f"❌ Ошибка проверки базовых ролей: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()
