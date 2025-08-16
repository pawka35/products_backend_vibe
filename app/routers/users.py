from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.models import User as UserModel, UserRole
from auth.schemas import UserResponse, UserList
from auth.utils import get_current_active_user
from auth.crud import get_users, get_user, get_users_by_role

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserList])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка всех пользователей (требует авторизации)
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение пользователя по ID (требует авторизации)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.get("/role/{role}", response_model=List[UserList])
async def get_users_by_role_endpoint(
    role: UserRole,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение пользователей по роли (требует авторизации)
    """
    users = get_users_by_role(db, role)
    return users[skip:skip + limit]
