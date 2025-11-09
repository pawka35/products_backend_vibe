from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from typing import Optional, List, Set
from auth.models import UserRole
from auth.validators import validate_password_strength
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.CUSTOMER
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v == UserRole.ADMIN:
            raise ValueError("Нельзя создать пользователя с ролью администратора через регистрацию")
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Пароль должен содержать минимум 8 символов")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    
    @field_validator('role')
    @classmethod
    def validate_role_update(cls, v):
        if v is not None and v == UserRole.ADMIN:
            raise ValueError("Нельзя изменить роль на администратора через обычное обновление")
        return v

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserResponse(BaseModel):
    """Схема для ответа API без валидации роли"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: EmailStr
    role: UserRole  # Основная роль (для обратной совместимости)
    roles: Optional[List[str]] = None  # Список всех ролей пользователя
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
        
    @classmethod
    def from_user(cls, user):
        """Создать схему из объекта User с поддержкой множественных ролей"""
        roles = None
        if hasattr(user, 'get_roles'):
            roles = list(user.get_roles())
        
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            roles=roles,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

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
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: EmailStr
    role: UserRole  # Основная роль (для обратной совместимости)
    roles: Optional[List[str]] = None  # Список всех ролей пользователя
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
        
    @classmethod
    def from_user(cls, user):
        """Создать схему из объекта User с поддержкой множественных ролей"""
        roles = None
        if hasattr(user, 'get_roles'):
            roles = list(user.get_roles())
        
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            roles=roles,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

class PasswordChange(BaseModel):
    """Схема для изменения пароля"""
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=8, max_length=128, description="Новый пароль")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

class UserProfileUpdate(BaseModel):
    """Схема для обновления профиля пользователя (без изменения роли)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "new_username",
                "email": "newemail@example.com"
            }
        }
    )
    
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Новое имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Новый email")

class UserUpdateResponse(BaseModel):
    """Схема ответа после обновления данных пользователя"""
    message: str
    user: UserResponse
