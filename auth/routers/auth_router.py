from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
from auth.models import User as UserModel, UserRole
from auth.schemas import (
    UserCreate, UserResponse, Token, PasswordChange, 
    UserProfileUpdate, UserUpdateResponse
)
from auth.crud import (
    create_user, authenticate_user, update_user_profile,
    change_user_password_with_verification
)
from auth.utils import create_access_token, get_current_active_user
from config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя
    """
    # Дополнительная проверка роли (на случай, если валидация схемы не сработает)
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Создание пользователей с ролью администратора запрещено"
        )
    
    # Проверяем, существует ли пользователь с таким username
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким именем уже существует"
        )
    
    # Проверяем, существует ли пользователь с таким email
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким email уже существует"
        )
    
    return create_user(db=db, user=user)

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Получение JWT токена для аутентификации
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserModel = Depends(get_current_active_user)):
    """
    Получение информации о текущем пользователе
    """
    return current_user

@router.put("/me", response_model=UserUpdateResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновление профиля текущего пользователя (username и/или email)
    
    - **username**: Новое имя пользователя (необязательно)
    - **email**: Новый email (необязательно)
    
    Оба поля необязательны, можно обновить только одно из них или оба сразу.
    """
    # Проверяем, что хотя бы одно поле для обновления указано
    if not profile_data.username and not profile_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Необходимо указать хотя бы одно поле для обновления"
        )
    
    try:
        updated_user = update_user_profile(
            db=db,
            user_id=current_user.id,
            username=profile_data.username,
            email=profile_data.email
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return UserUpdateResponse(
            message="Профиль успешно обновлен",
            user=updated_user
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/me/password", response_model=UserUpdateResponse)
async def change_my_password(
    password_data: PasswordChange,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Изменение пароля текущего пользователя
    
    - **current_password**: Текущий пароль для подтверждения
    - **new_password**: Новый пароль (минимум 8 символов)
    
    Новый пароль должен соответствовать требованиям безопасности:
    - Минимум 8 символов
    - Содержать заглавные и строчные буквы
    - Содержать цифры
    - Содержать специальные символы
    """
    try:
        updated_user = change_user_password_with_verification(
            db=db,
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return UserUpdateResponse(
            message="Пароль успешно изменен",
            user=updated_user
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
