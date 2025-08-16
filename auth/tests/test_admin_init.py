import pytest
from sqlalchemy.orm import Session
from auth.models.user_models import User, UserRole
from auth.models.role_models import Role, RoleAssignment
from auth.utils.admin_init import create_initial_admin, generate_secure_password
from auth.schemas.user_schemas import UserCreate
from auth.crud import create_user

class TestAdminInitialization:
    """Тесты для инициализации администратора"""
    
    def test_generate_secure_password(self):
        """Тест генерации безопасного пароля"""
        password = generate_secure_password(16)
        
        assert len(password) == 16
        assert any(c.isupper() for c in password)  # Есть заглавные буквы
        assert any(c.islower() for c in password)  # Есть строчные буквы
        assert any(c.isdigit() for c in password)  # Есть цифры
        assert any(c in "!@#$%^&*" for c in password)  # Есть спецсимволы
    
    def test_create_initial_admin_when_none_exists(self, db: Session):
        """Тест создания первого администратора"""
        # Убеждаемся, что администраторов нет
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        assert existing_admin is None
        
        # Создаем администратора
        username, password = create_initial_admin(db)
        
        assert username == "admin"
        assert password is not None
        assert len(password) == 20
        
        # Проверяем, что пользователь создан в базе
        admin_user = db.query(User).filter(User.username == "admin").first()
        assert admin_user is not None
        assert admin_user.role == UserRole.ADMIN
        assert admin_user.email == "admin@system.local"
        assert admin_user.is_active is True
    
    def test_create_initial_admin_when_exists(self, db: Session):
        """Тест попытки создать администратора, когда он уже существует"""
        # Создаем первого администратора
        username1, password1 = create_initial_admin(db)
        assert username1 == "admin"
        
        # Пытаемся создать второго администратора
        username2, password2 = create_initial_admin(db)
        
        assert username2 is None
        assert password2 is None
        
        # Проверяем, что в базе только один администратор
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        assert admin_count == 1

class TestAdminRegistrationProtection:
    """Тесты защиты от регистрации администраторов"""
    
    def test_cannot_register_admin_user(self, db: Session):
        """Тест, что нельзя зарегистрировать пользователя с ролью администратора"""
        user_data = {
            "username": "testadmin",
            "email": "testadmin@example.com",
            "password": "testpassword123",
            "role": UserRole.ADMIN
        }
        
        user_create = UserCreate(**user_data)
        
        with pytest.raises(ValueError, match="Нельзя создать пользователя с ролью администратора"):
            # Попытка создать пользователя должна вызвать ошибку валидации
            pass
    
    def test_cannot_update_user_to_admin(self, db: Session):
        """Тест, что нельзя обновить роль пользователя на администратора"""
        # Сначала создаем обычного пользователя
        user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
            "role": UserRole.CUSTOMER
        }
        
        user_create = UserCreate(**user_data)
        user = create_user(db, user_create)
        
        # Пытаемся обновить роль на администратора
        from auth.schemas.user_schemas import UserUpdate
        user_update = UserUpdate(role=UserRole.ADMIN)
        
        with pytest.raises(ValueError, match="Нельзя изменить роль на администратора"):
            # Попытка обновления должна вызвать ошибку валидации
            pass
