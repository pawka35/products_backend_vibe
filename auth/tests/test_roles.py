import pytest
from sqlalchemy.orm import Session
from auth.models.role_models import Role, RoleAssignment
from auth.models.user_models import User, UserRole as UserRoleEnum
from auth.crud.role_crud import role_crud, role_assignment_crud
from auth.schemas.role_schemas import RoleCreate, RoleUpdate, RoleAssignmentCreate
from auth.utils.auth_utils import create_access_token
from database import get_db

class TestRoleCRUD:
    """Тесты для CRUD операций с ролями"""
    
    @pytest.fixture
    def sample_role_data(self):
        """Тестовые данные для роли"""
        return {
            "name": "test_role",
            "description": "Тестовая роль",
            "permissions": '{"read": true, "write": false}',
            "is_active": True
        }
    
    @pytest.fixture
    def sample_user(self, db: Session):
        """Тестовый пользователь"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            role=UserRoleEnum.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def test_create_role(self, db: Session, sample_role_data, sample_user):
        """Тест создания роли"""
        role_create = RoleCreate(**sample_role_data)
        role = role_crud.create_role(db, role_create, sample_user.id)
        
        assert role.name == sample_role_data["name"]
        assert role.description == sample_role_data["description"]
        assert role.permissions == sample_role_data["permissions"]
        assert role.is_active == sample_role_data["is_active"]
        assert role.id is not None
    
    def test_get_role(self, db: Session, sample_role_data, sample_user):
        """Тест получения роли по ID"""
        role_create = RoleCreate(**sample_role_data)
        created_role = role_crud.create_role(db, role_create, sample_user.id)
        
        retrieved_role = role_crud.get_role(db, created_role.id)
        assert retrieved_role is not None
        assert retrieved_role.name == created_role.name
    
    def test_get_role_by_name(self, db: Session, sample_role_data, sample_user):
        """Тест получения роли по названию"""
        role_create = RoleCreate(**sample_role_data)
        created_role = role_crud.create_role(db, role_create, sample_user.id)
        
        retrieved_role = role_crud.get_role_by_name(db, created_role.name)
        assert retrieved_role is not None
        assert retrieved_role.id == created_role.id
    
    def test_update_role(self, db: Session, sample_role_data, sample_user):
        """Тест обновления роли"""
        role_create = RoleCreate(**sample_role_data)
        created_role = role_crud.create_role(db, role_create, sample_user.id)
        
        role_update = RoleUpdate(description="Обновленное описание")
        updated_role = role_crud.update_role(db, created_role.id, role_update)
        
        assert updated_role.description == "Обновленное описание"
        assert updated_role.name == created_role.name  # Не изменилось
    
    def test_delete_role(self, db: Session, sample_role_data, sample_user):
        """Тест удаления роли"""
        role_create = RoleCreate(**sample_role_data)
        created_role = role_crud.create_role(db, role_create, sample_user.id)
        
        success = role_crud.delete_role(db, created_role.id)
        assert success is True
        
        # Проверяем, что роль деактивирована
        deleted_role = role_crud.get_role(db, created_role.id)
        assert deleted_role.is_active is False

class TestRoleAssignmentCRUD:
    """Тесты для CRUD операций с назначением ролей пользователям"""
    
    @pytest.fixture
    def sample_role(self, db: Session, sample_user):
        """Тестовая роль"""
        role_data = {
            "name": "customer_role",
            "description": "Роль покупателя",
            "is_active": True
        }
        role_create = RoleCreate(**role_data)
        return role_crud.create_role(db, role_create, sample_user.id)
    
    @pytest.fixture
    def sample_customer(self, db: Session):
        """Тестовый покупатель"""
        user = User(
            username="customer",
            email="customer@example.com",
            hashed_password="hashed_password",
            role=UserRoleEnum.CUSTOMER,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def test_assign_role_to_user(self, db: Session, sample_role, sample_customer, sample_user):
        """Тест назначения роли пользователю"""
        role_assignment_create = RoleAssignmentCreate(
            user_id=sample_customer.id,
            role_id=sample_role.id
        )
        
        role_assignment = role_assignment_crud.assign_role_to_user(
            db, role_assignment_create, sample_user.id
        )
        
        assert role_assignment.user_id == sample_customer.id
        assert role_assignment.role_id == sample_role.id
        assert role_assignment.assigned_by == sample_user.id
        assert role_assignment.is_active is True
    
    def test_assign_duplicate_role(self, db: Session, sample_role, sample_customer, sample_user):
        """Тест попытки назначить уже существующую роль"""
        role_assignment_create = RoleAssignmentCreate(
            user_id=sample_customer.id,
            role_id=sample_role.id
        )
        
        # Назначаем роль первый раз
        role_assignment_crud.assign_role_to_user(db, role_assignment_create, sample_user.id)
        
        # Пытаемся назначить ту же роль снова
        with pytest.raises(ValueError, match="Роль уже назначена пользователю"):
            role_assignment_crud.assign_role_to_user(db, role_assignment_create, sample_user.id)
    
    def test_get_user_roles(self, db: Session, sample_role, sample_customer, sample_user):
        """Тест получения ролей пользователя"""
        role_assignment_create = RoleAssignmentCreate(
            user_id=sample_customer.id,
            role_id=sample_role.id
        )
        role_assignment_crud.assign_role_to_user(db, role_assignment_create, sample_user.id)
        
        user_roles = role_assignment_crud.get_user_roles(db, sample_customer.id)
        assert len(user_roles) == 1
        assert user_roles[0].role_id == sample_role.id
    
    def test_remove_role_from_user(self, db: Session, sample_role, sample_customer, sample_user):
        """Тест удаления роли у пользователя"""
        role_assignment_create = RoleAssignmentCreate(
            user_id=sample_customer.id,
            role_id=sample_role.id
        )
        role_assignment = role_assignment_crud.assign_role_to_user(db, role_assignment_create, sample_user.id)
        
        success = role_assignment_crud.remove_role_from_user(db, role_assignment.id)
        assert success is True
        
        # Проверяем, что роль деактивирована
        user_roles = role_assignment_crud.get_user_roles(db, sample_customer.id, active_only=True)
        assert len(user_roles) == 0

class TestRolePermissions:
    """Тесты для проверки прав доступа к ролям"""
    
    def test_admin_can_create_role(self, db: Session, sample_user):
        """Тест, что администратор может создавать роли"""
        role_data = {
            "name": "new_role",
            "description": "Новая роль",
            "is_active": True
        }
        role_create = RoleCreate(**role_data)
        role = role_crud.create_role(db, role_create, sample_user.id)
        
        assert role is not None
        assert role.name == "new_role"
    
    def test_role_name_uniqueness(self, db: Session, sample_user):
        """Тест уникальности названий ролей"""
        role_data = {
            "name": "unique_role",
            "description": "Уникальная роль",
            "is_active": True
        }
        role_create = RoleCreate(**role_data)
        
        # Создаем первую роль
        role_crud.create_role(db, role_create, sample_user.id)
        
        # Пытаемся создать роль с тем же названием
        with pytest.raises(Exception):  # Должна быть ошибка уникальности
            role_crud.create_role(db, role_create, sample_user.id)
