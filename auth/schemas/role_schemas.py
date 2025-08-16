from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RoleBase(BaseModel):
    """Базовая схема роли"""
    name: str = Field(..., min_length=1, max_length=50, description="Название роли")
    description: Optional[str] = Field(None, max_length=500, description="Описание роли")
    permissions: Optional[str] = Field(None, description="JSON строка с правами")
    is_active: bool = Field(True, description="Активна ли роль")

class RoleCreate(RoleBase):
    """Схема для создания роли"""
    pass

class RoleUpdate(BaseModel):
    """Схема для обновления роли"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[str] = None
    is_active: Optional[bool] = None

class Role(RoleBase):
    """Схема роли с полной информацией"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserRoleBase(BaseModel):
    """Базовая схема связи пользователя с ролью"""
    user_id: int = Field(..., description="ID пользователя")
    role_id: int = Field(..., description="ID роли")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения роли")
    is_active: bool = Field(True, description="Активна ли связь")

class UserRoleCreate(UserRoleBase):
    """Схема для создания связи пользователя с ролью"""
    pass

class UserRoleUpdate(BaseModel):
    """Схема для обновления связи пользователя с ролью"""
    role_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class UserRole(UserRoleBase):
    """Схема связи пользователя с ролью с полной информацией"""
    id: int
    assigned_by: Optional[int] = None
    assigned_at: datetime
    
    class Config:
        from_attributes = True

class UserRoleDetail(UserRole):
    """Детальная схема связи пользователя с ролью"""
    role: Role
    assigned_by_user: Optional[str] = Field(None, description="Имя пользователя, назначившего роль")

class RoleWithUsers(Role):
    """Роль с информацией о пользователях"""
    users_count: int = Field(0, description="Количество пользователей с этой ролью")

class UserWithRoles(BaseModel):
    """Пользователь с ролями"""
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    user_roles: List[UserRoleDetail] = []
    
    class Config:
        from_attributes = True
