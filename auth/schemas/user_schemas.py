from pydantic import BaseModel, EmailStr
from typing import Optional
from auth.models import UserRole
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.CUSTOMER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None

class User(UserBase):
    id: int
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
