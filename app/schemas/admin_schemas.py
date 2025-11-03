from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from auth.models import UserRole
from auth.schemas import UserResponse
from auth.validators import validate_password_strength

class ChangePasswordRequest(BaseModel):
    new_password: str

class ChangeRoleRequest(BaseModel):
    new_role: UserRole

class UserManagementResponse(BaseModel):
    message: str
    user: Optional[UserResponse] = None

class UserStatistics(BaseModel):
    total_users: int
    users_by_role: dict[str, int]

class BulkUserOperation(BaseModel):
    user_ids: list[int]
    operation: str  # "change_role", "deactivate", etc.
    new_role: Optional[UserRole] = None

class AdminUserCreate(BaseModel):
    """Схема для создания пользователя администратором (без ограничений на роль)"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=8, max_length=128, description="Пароль пользователя")
    role: UserRole = Field(UserRole.CUSTOMER, description="Роль пользователя (admin, customer, executor)")
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v
