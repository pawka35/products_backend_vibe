from sqlalchemy.orm import Session
from auth.models import User, UserRole
from auth.utils import get_password_hash

def create_user_by_admin(db: Session, username: str, email: str, password: str, role: UserRole):
    """Создание пользователя администратором (с возможностью указать любую роль)"""
    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def change_user_password(db: Session, user_id: int, new_password: str):
    """Изменение пароля пользователя"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(db_user)
    return db_user

def change_user_role(db: Session, user_id: int, new_role: UserRole):
    """Изменение роли пользователя"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    db_user.role = new_role
    db.commit()
    db.refresh(db_user)
    return db_user

def deactivate_user(db: Session, user_id: int):
    """Деактивация пользователя (можно добавить поле is_active в модель)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    # Для простоты просто удаляем пользователя
    # В реальном проекте лучше добавить поле is_active
    db.delete(db_user)
    db.commit()
    return True

def get_user_statistics(db: Session):
    """Получение статистики по пользователям"""
    total_users = db.query(User).count()
    users_by_role = {}
    
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        users_by_role[role.value] = count
    
    return {
        "total_users": total_users,
        "users_by_role": users_by_role
    }
