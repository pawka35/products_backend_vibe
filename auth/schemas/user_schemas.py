from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from auth.models import UserRole
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.CUSTOMER
    
    @validator('role')
    def validate_role(cls, v):
        if v == UserRole.ADMIN:
            raise ValueError("Нельзя создать пользователя с ролью администратора через регистрацию")
        return v

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    
    @validator('role')
    def validate_role_update(cls, v):
        if v == UserRole.ADMIN:
            raise ValueError("Нельзя изменить роль на администратора через обычное обновление")
        return v

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """Схема для ответа API без валидации роли"""
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserList(BaseModel):
    """Схема для списка пользователей без валидации роли"""
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
