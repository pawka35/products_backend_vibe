from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from auth.models.role_models import Role, UserRole
from auth.models.user_models import User
from auth.schemas.role_schemas import RoleCreate, RoleUpdate, UserRoleCreate, UserRoleUpdate

class RoleCRUD:
    """CRUD операции для ролей"""
    
    def create_role(self, db: Session, role: RoleCreate, created_by: int) -> Role:
        """Создание новой роли"""
        db_role = Role(**role.dict())
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return db_role
    
    def get_role(self, db: Session, role_id: int) -> Optional[Role]:
        """Получение роли по ID"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, db: Session, name: str) -> Optional[Role]:
        """Получение роли по названию"""
        return db.query(Role).filter(Role.name == name).first()
    
    def get_roles(self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Role]:
        """Получение списка ролей"""
        query = db.query(Role)
        if active_only:
            query = query.filter(Role.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    def get_roles_with_users_count(self, db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        """Получение ролей с количеством пользователей"""
        result = db.query(
            Role,
            func.count(UserRole.user_id).label('users_count')
        ).outerjoin(UserRole, and_(Role.id == UserRole.role_id, UserRole.is_active == True))\
         .group_by(Role.id)\
         .offset(skip)\
         .limit(limit)\
         .all()
        
        return [
            {
                "role": role,
                "users_count": users_count
            }
            for role, users_count in result
        ]
    
    def update_role(self, db: Session, role_id: int, role_update: RoleUpdate) -> Optional[Role]:
        """Обновление роли"""
        db_role = self.get_role(db, role_id)
        if not db_role:
            return None
        
        update_data = role_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role, field, value)
        
        db.commit()
        db.refresh(db_role)
        return db_role
    
    def delete_role(self, db: Session, role_id: int) -> bool:
        """Удаление роли (мягкое удаление - деактивация)"""
        db_role = self.get_role(db, role_id)
        if not db_role:
            return False
        
        # Проверяем, есть ли пользователи с этой ролью
        users_with_role = db.query(UserRole).filter(
            and_(UserRole.role_id == role_id, UserRole.is_active == True)
        ).count()
        
        if users_with_role > 0:
            # Если есть пользователи, деактивируем роль
            db_role.is_active = False
        else:
            # Если нет пользователей, удаляем полностью
            db.delete(db_role)
        
        db.commit()
        return True
    
    def activate_role(self, db: Session, role_id: int) -> bool:
        """Активация роли"""
        db_role = self.get_role(db, role_id)
        if not db_role:
            return False
        
        db_role.is_active = True
        db.commit()
        db.refresh(db_role)
        return True

class UserRoleCRUD:
    """CRUD операции для связи пользователей с ролями"""
    
    def assign_role_to_user(self, db: Session, user_role: UserRoleCreate, assigned_by: int) -> UserRole:
        """Назначение роли пользователю"""
        # Проверяем, не назначена ли уже эта роль
        existing_role = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_role.user_id,
                UserRole.role_id == user_role.role_id,
                UserRole.is_active == True
            )
        ).first()
        
        if existing_role:
            raise ValueError("Роль уже назначена пользователю")
        
        db_user_role = UserRole(**user_role.dict(), assigned_by=assigned_by)
        db.add(db_user_role)
        db.commit()
        db.refresh(db_user_role)
        return db_user_role
    
    def get_user_roles(self, db: Session, user_id: int, active_only: bool = True) -> List[UserRole]:
        """Получение ролей пользователя"""
        query = db.query(UserRole).filter(UserRole.user_id == user_id)
        if active_only:
            query = query.filter(UserRole.is_active == True)
        return query.all()
    
    def get_user_role(self, db: Session, user_role_id: int) -> Optional[UserRole]:
        """Получение конкретной связи пользователя с ролью"""
        return db.query(UserRole).filter(UserRole.id == user_role_id).first()
    
    def update_user_role(self, db: Session, user_role_id: int, user_role_update: UserRoleUpdate) -> Optional[UserRole]:
        """Обновление связи пользователя с ролью"""
        db_user_role = self.get_user_role(db, user_role_id)
        if not db_user_role:
            return None
        
        update_data = user_role_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user_role, field, value)
        
        db.commit()
        db.refresh(db_user_role)
        return db_user_role
    
    def remove_role_from_user(self, db: Session, user_role_id: int) -> bool:
        """Удаление роли у пользователя (мягкое удаление)"""
        db_user_role = self.get_user_role(db, user_role_id)
        if not db_user_role:
            return False
        
        db_user_role.is_active = False
        db.commit()
        return True
    
    def get_users_by_role(self, db: Session, role_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение пользователей по роли"""
        return db.query(User).join(UserRole).filter(
            and_(UserRole.role_id == role_id, UserRole.is_active == True)
        ).offset(skip).limit(limit).all()
    
    def get_user_roles_detailed(self, db: Session, user_id: int) -> List[dict]:
        """Получение детальной информации о ролях пользователя"""
        result = db.query(
            UserRole,
            Role,
            User.username.label('assigned_by_username')
        ).join(Role, UserRole.role_id == Role.id)\
         .outerjoin(User, UserRole.assigned_by == User.id)\
         .filter(UserRole.user_id == user_id)\
         .all()
        
        return [
            {
                "user_role": user_role,
                "role": role,
                "assigned_by_username": assigned_by_username
            }
            for user_role, role, assigned_by_username in result
        ]

# Создаем экземпляры для использования
role_crud = RoleCRUD()
user_role_crud = UserRoleCRUD()
