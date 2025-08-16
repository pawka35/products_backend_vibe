from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from auth.utils.admin_auth import get_current_admin_user, check_user_permissions
from auth.models.user_models import User
from auth.crud.role_crud import role_crud, role_assignment_crud
from auth.schemas.role_schemas import (
    Role, RoleCreate, RoleUpdate, 
    RoleAssignment, RoleAssignmentCreate, RoleAssignmentUpdate,
    RoleWithUsers, UserWithRoles
)
from auth.schemas.user_schemas import User as UserSchema

router = APIRouter(prefix="/admin/roles", tags=["admin-roles"])

# ==================== УПРАВЛЕНИЕ РОЛЯМИ ====================

@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Создание новой роли (только для администраторов)
    """
    # Проверяем, не существует ли уже роль с таким именем
    existing_role = role_crud.get_role_by_name(db, role.name)
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Роль с названием '{role.name}' уже существует."
        )
    
    return role_crud.create_role(db, role, current_user.id)

@router.get("/", response_model=List[RoleWithUsers])
async def get_roles(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    active_only: bool = Query(True, description="Только активные роли"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка ролей с количеством пользователей (только для администраторов)
    """
    # Всегда используем метод с количеством пользователей для единообразия
    roles_with_count = role_crud.get_roles_with_users_count(db, skip, limit)
    
    # Если нужны только активные роли, фильтруем результат
    if active_only:
        roles_with_count = [
            item for item in roles_with_count 
            if item["is_active"]
        ]
    
    return roles_with_count

@router.get("/{role_id}", response_model=Role)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Получение роли по ID (только для администраторов)
    """
    role = role_crud.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена."
        )
    return role

@router.put("/{role_id}", response_model=Role)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Обновление роли (только для администраторов)
    """
    # Проверяем, не пытается ли администратор изменить системные роли
    role = role_crud.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена."
        )
    
    # Проверяем, не пытается ли изменить название на уже существующее
    if role_update.name and role_update.name != role.name:
        existing_role = role_crud.get_role_by_name(db, role_update.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Роль с названием '{role_update.name}' уже существует."
            )
    
    updated_role = role_crud.update_role(db, role_id, role_update)
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена."
        )
    
    return updated_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Удаление роли (только для администраторов)
    """
    # Проверяем, не пытается ли администратор удалить системные роли
    role = role_crud.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена."
        )
    
    # Проверяем, не пытается ли удалить роль admin
    if role.name == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить системную роль 'admin'."
        )
    
    success = role_crud.delete_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить роль."
        )

@router.post("/{role_id}/activate", response_model=Role)
async def activate_role(
    role_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Активация роли (только для администраторов)
    """
    success = role_crud.activate_role(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена."
        )
    
    return role_crud.get_role(db, role_id)

# ==================== УПРАВЛЕНИЕ РОЛЯМИ ПОЛЬЗОВАТЕЛЕЙ ====================

@router.post("/users/assign", response_model=RoleAssignment, status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    role_assignment: RoleAssignmentCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Назначение роли пользователю (только для администраторов)
    """
    # Проверяем права на управление целевым пользователем
    check_user_permissions(role_assignment.user_id, current_user, db)
    
    try:
        return role_assignment_crud.assign_role_to_user(db, role_assignment, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/users/{user_id}", response_model=List[RoleAssignment])
async def get_user_roles(
    user_id: int,
    active_only: bool = Query(True, description="Только активные роли"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Получение ролей пользователя (только для администраторов)
    """
    # Проверяем права на просмотр целевого пользователя
    check_user_permissions(user_id, current_user, db)
    
    return role_assignment_crud.get_user_roles(db, user_id, active_only)

@router.get("/users/{user_id}/detailed", response_model=List[dict])
async def get_user_roles_detailed(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Получение детальной информации о ролях пользователя (только для администраторов)
    """
    # Проверяем права на просмотр целевого пользователя
    check_user_permissions(user_id, current_user, db)
    
    return role_assignment_crud.get_user_roles_detailed(db, user_id)

@router.put("/users/{role_assignment_id}", response_model=RoleAssignment)
async def update_user_role(
    role_assignment_id: int,
    role_assignment_update: RoleAssignmentUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Обновление роли пользователя (только для администраторов)
    """
    # Получаем текущую связь пользователя с ролью
    current_role_assignment = role_assignment_crud.get_role_assignment(db, role_assignment_id)
    if not current_role_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь пользователя с ролью не найдена."
        )
    
    # Проверяем права на управление целевым пользователем
    check_user_permissions(current_role_assignment.user_id, current_user, db)
    
    # Если меняется роль, проверяем, не назначается ли уже эта роль
    if role_assignment_update.role_id and role_assignment_update.role_id != current_role_assignment.role_id:
        existing_role = role_assignment_crud.get_role_assignment(db, role_assignment_id)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Эта роль уже назначена пользователю."
            )
    
    updated_role_assignment = role_assignment_crud.update_role_assignment(db, role_assignment_id, role_assignment_update)
    if not updated_role_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь пользователя с ролью не найдена."
        )
    
    return updated_role_assignment

@router.delete("/users/{role_assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    role_assignment_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Удаление роли у пользователя (только для администраторов)
    """
    # Получаем текущую связь пользователя с ролью
    current_role_assignment = role_assignment_crud.get_role_assignment(db, role_assignment_id)
    if not current_role_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь пользователя с ролью не найдена."
        )
    
    # Проверяем права на управление целевым пользователем
    check_user_permissions(current_role_assignment.user_id, current_user, db)
    
    # Проверяем, не пытается ли удалить роль admin у пользователя
    if current_role_assignment.role.name == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить системную роль 'admin' у пользователя."
        )
    
    success = role_assignment_crud.remove_role_from_user(db, role_assignment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось удалить роль у пользователя."
        )

@router.get("/{role_id}/users", response_model=List[UserSchema])
async def get_users_by_role(
    role_id: int,
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Получение пользователей по роли (только для администраторов)
    """
    # Проверяем, существует ли роль
    role = role_crud.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена."
        )
    
    return role_assignment_crud.get_users_by_role(db, role_id, skip, limit)
