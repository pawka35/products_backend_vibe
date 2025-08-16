from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from auth.utils.admin_auth import get_current_admin_user, check_user_permissions
from auth.models.user_models import User

router = APIRouter(prefix="/admin/roles", tags=["admin-roles"])

@router.get("/test")
async def test_roles_endpoint(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Простой тестовый эндпоинт для проверки работы роутера ролей
    """
    return {
        "message": "Роутер ролей работает!",
        "user": current_user.username,
        "role": current_user.role
    }

@router.get("/")
async def get_roles_basic(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Базовое получение списка ролей (только для администраторов)
    """
    # Временно возвращаем простой ответ
    return [
        {
            "id": 1,
            "name": "admin",
            "description": "Системная роль администратора",
            "is_active": True,
            "users_count": 1
        },
        {
            "id": 2,
            "name": "customer",
            "description": "Роль покупателя",
            "is_active": True,
            "users_count": 2
        },
        {
            "id": 3,
            "name": "executor",
            "description": "Роль исполнителя заказов",
            "is_active": True,
            "users_count": 0
        }
    ]
