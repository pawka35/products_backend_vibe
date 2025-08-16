from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from auth.utils.auth_utils import get_current_user
from auth.models.user_models import User, UserRole
from database import get_db
from typing import Optional

security = HTTPBearer()

def get_current_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Проверяет, что текущий пользователь является администратором
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуется роль администратора."
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован."
        )
    
    return current_user

def get_current_super_admin_user(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Проверяет, что текущий пользователь является супер-администратором
    (может управлять другими администраторами)
    """
    # Здесь можно добавить дополнительную логику для супер-администраторов
    # Например, проверка специального флага или дополнительной роли
    
    # Пока что просто проверяем, что это администратор
    return current_user

def check_user_permissions(
    target_user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Проверяет, может ли текущий администратор управлять целевым пользователем
    """
    # Администратор не может управлять собой
    if target_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя управлять собственными ролями."
        )
    
    # Получаем целевого пользователя
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден."
        )
    
    # Проверяем, не пытается ли обычный администратор управлять другим администратором
    if target_user.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для управления администраторами."
        )
    
    return True

def get_admin_user_with_optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Получает пользователя-администратора, если передан токен, иначе None
    Полезно для эндпоинтов, которые могут работать как с авторизацией, так и без
    """
    if not credentials:
        return None
    
    try:
        current_user = get_current_user(credentials, db)
        if current_user.role == UserRole.ADMIN and current_user.is_active:
            return current_user
    except:
        pass
    
    return None
