from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from auth.models import UserRole
from auth.validators import validate_password_strength
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
    password: str = Field(..., min_length=8, max_length=128, description="Пароль должен содержать минимум 8 символов")
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

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

class PasswordChange(BaseModel):
    """Схема для изменения пароля"""
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, max_length=128, description="Новый пароль")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

class UserProfileUpdate(BaseModel):
    """Схема для обновления профиля пользователя (без изменения роли)"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Новое имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Новый email")
    
    class Config:
        schema_extra = {
            "example": {
                "username": "new_username",
                "email": "newemail@example.com"
            }
        }

class UserUpdateResponse(BaseModel):
    """Схема ответа после обновления данных пользователя"""
    message: str
    user: UserResponse
