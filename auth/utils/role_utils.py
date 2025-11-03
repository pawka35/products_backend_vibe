"""
Утилиты для работы с множественными ролями пользователей
"""
from typing import List, Set
from fastapi import HTTPException, status
from auth.models import User as UserModel, UserRole


def get_user_roles(user: UserModel) -> Set[str]:
    """
    Получить все активные роли пользователя.
    
    Args:
        user: Объект пользователя
        
    Returns:
        Set из названий ролей
    """
    if hasattr(user, 'get_roles'):
        return user.get_roles()
    # Fallback на старую систему
    return {user.role.value}


def user_has_role(user: UserModel, role_name: str) -> bool:
    """
    Проверить, имеет ли пользователь указанную роль.
    
    Args:
        user: Объект пользователя
        role_name: Название роли для проверки
        
    Returns:
        True если пользователь имеет роль, иначе False
    """
    if hasattr(user, 'has_role'):
        return user.has_role(role_name)
    # Fallback на старую систему
    return user.role.value == role_name or user.role.value.lower() == role_name.lower()


def user_has_any_role(user: UserModel, role_names: List[str]) -> bool:
    """
    Проверить, имеет ли пользователь хотя бы одну из указанных ролей.
    
    Args:
        user: Объект пользователя
        role_names: Список названий ролей для проверки
        
    Returns:
        True если пользователь имеет хотя бы одну из ролей, иначе False
    """
    if hasattr(user, 'has_any_role'):
        return user.has_any_role(role_names)
    # Fallback на старую систему
    user_role = user.role.value
    return any(user_role == role or user_role.lower() == role.lower() for role in role_names)


def require_roles(allowed_roles: List[str], error_message: str = None):
    """
    Декоратор/функция для проверки наличия у пользователя одной из требуемых ролей.
    
    Args:
        allowed_roles: Список разрешенных ролей
        error_message: Кастомное сообщение об ошибке
        
    Returns:
        Функция для проверки пользователя
    """
    def check_user_roles(user: UserModel) -> UserModel:
        if not user_has_any_role(user, allowed_roles):
            if error_message:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_message
                )
            else:
                roles_str = ", ".join(allowed_roles)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Требуется одна из ролей: {roles_str}"
                )
        return user
    
    return check_user_roles


def is_admin(user: UserModel) -> bool:
    """
    Проверить, является ли пользователь администратором.
    
    Args:
        user: Объект пользователя
        
    Returns:
        True если пользователь администратор, иначе False
    """
    if hasattr(user, 'is_admin'):
        return user.is_admin()
    return user.role == UserRole.ADMIN


def is_customer(user: UserModel) -> bool:
    """
    Проверить, является ли пользователь заказчиком.
    
    Args:
        user: Объект пользователя
        
    Returns:
        True если пользователь заказчик, иначе False
    """
    if hasattr(user, 'is_customer'):
        return user.is_customer()
    return user.role == UserRole.CUSTOMER


def is_executor(user: UserModel) -> bool:
    """
    Проверить, является ли пользователь исполнителем.
    
    Args:
        user: Объект пользователя
        
    Returns:
        True если пользователь исполнитель, иначе False
    """
    if hasattr(user, 'is_executor'):
        return user.is_executor()
    return user.role == UserRole.EXECUTOR


def has_customer_access(user: UserModel) -> bool:
    """
    Проверить, имеет ли пользователь доступ к функционалу заказчика.
    Администраторы также имеют доступ.
    
    Args:
        user: Объект пользователя
        
    Returns:
        True если пользователь имеет доступ, иначе False
    """
    return user_has_any_role(user, ["customer", "admin"])


def has_executor_access(user: UserModel) -> bool:
    """
    Проверить, имеет ли пользователь доступ к функционалу исполнителя.
    Администраторы также имеют доступ.
    
    Args:
        user: Объект пользователя
        
    Returns:
        True если пользователь имеет доступ, иначе False
    """
    return user_has_any_role(user, ["executor", "admin"])


def has_admin_access(user: UserModel) -> bool:
    """
    Проверить, имеет ли пользователь административный доступ.
    
    Args:
        user: Объект пользователя
        
    Returns:
        True если пользователь администратор, иначе False
    """
    return is_admin(user)

