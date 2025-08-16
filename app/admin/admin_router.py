from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.models import User as UserModel, UserRole
from auth.schemas import User as UserSchema
from auth.utils import get_current_active_user
from auth.crud import get_users, get_user, get_users_by_role
from app.crud import (
    change_user_password,
    change_user_role,
    deactivate_user,
    get_user_statistics
)
from app.schemas import (
    ChangePasswordRequest,
    ChangeRoleRequest,
    UserManagementResponse,
    UserStatistics,
    BulkUserOperation
)

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(current_user: UserModel = Depends(get_current_active_user)):
    """Проверка, что пользователь является администратором"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user

@router.get("/users", response_model=List[UserSchema])
async def admin_get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение списка всех пользователей (только для администраторов)
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserSchema)
async def admin_get_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение конкретного пользователя (только для администраторов)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.put("/users/{user_id}/password", response_model=UserManagementResponse)
async def admin_change_user_password(
    user_id: int,
    password_data: ChangePasswordRequest,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Изменение пароля пользователя (только для администраторов)
    """
    updated_user = change_user_password(db, user_id, password_data.new_password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserManagementResponse(
        message="Пароль пользователя успешно изменен",
        user=updated_user
    )

@router.put("/users/{user_id}/role", response_model=UserManagementResponse)
async def admin_change_user_role(
    user_id: int,
    role_data: ChangeRoleRequest,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Изменение роли пользователя (только для администраторов)
    """
    updated_user = change_user_role(db, user_id, role_data.new_role)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserManagementResponse(
        message="Роль пользователя успешно изменена",
        user=updated_user
    )

@router.delete("/users/{user_id}", response_model=UserManagementResponse)
async def admin_deactivate_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Деактивация пользователя (только для администраторов)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя деактивировать самого себя"
        )
    
    result = deactivate_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserManagementResponse(
        message="Пользователь успешно деактивирован"
    )

@router.get("/users/role/{role}", response_model=List[UserSchema])
async def admin_get_users_by_role(
    role: UserRole,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение пользователей по роли (только для администраторов)
    """
    users = get_users_by_role(db, role)
    return users[skip:skip + limit]

@router.get("/statistics", response_model=UserStatistics)
async def admin_get_statistics(
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение статистики по пользователям (только для администраторов)
    """
    return get_user_statistics(db)

@router.post("/users/bulk/change-role", response_model=UserManagementResponse)
async def admin_bulk_change_role(
    bulk_data: BulkUserOperation,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Массовое изменение ролей пользователей (только для администраторов)
    """
    if bulk_data.operation == "change_role" and bulk_data.new_role:
        changed_count = 0
        for user_id in bulk_data.user_ids:
            if user_id != current_user.id:  # Нельзя изменить свою роль
                result = change_user_role(db, user_id, bulk_data.new_role)
                if result:
                    changed_count += 1
        
        return UserManagementResponse(
            message=f"Роли изменены для {changed_count} пользователей"
        )
    
    raise HTTPException(
        status_code=400, 
        detail="Неподдерживаемая операция"
    )
