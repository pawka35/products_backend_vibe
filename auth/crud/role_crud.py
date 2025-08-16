from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from auth.models.role_models import Role, RoleAssignment
from auth.models.user_models import User
from auth.schemas.role_schemas import RoleCreate, RoleUpdate, RoleAssignmentCreate, RoleAssignmentUpdate

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
        # Используем raw SQL для избежания проблем с связями
        result = db.execute("""
            SELECT r.id, r.name, r.description, r.permissions, r.is_active, r.created_at, r.updated_at,
                   COUNT(ur.user_id) as users_count
            FROM roles r
            LEFT JOIN user_roles ur ON r.id = ur.role_id AND ur.is_active = 1
            GROUP BY r.id
            LIMIT :limit OFFSET :skip
        """, {"limit": limit, "skip": skip})
        
        roles_with_count = []
        for row in result:
            role = Role(
                id=row.id,
                name=row.name,
                description=row.description,
                permissions=row.permissions,
                is_active=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            roles_with_count.append({
                "role": role,
                "users_count": row.users_count
            })
        
        return roles_with_count
    
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
        users_with_role = db.query(RoleAssignment).filter(
            and_(RoleAssignment.role_id == role_id, RoleAssignment.is_active == True)
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

class RoleAssignmentCRUD:
    """CRUD операции для связи пользователей с ролями"""
    
    def assign_role_to_user(self, db: Session, role_assignment: RoleAssignmentCreate, assigned_by: int) -> RoleAssignment:
        """Назначение роли пользователю"""
        # Проверяем, не назначена ли уже эта роль
        existing_role = db.query(RoleAssignment).filter(
            and_(
                RoleAssignment.user_id == role_assignment.user_id,
                RoleAssignment.role_id == role_assignment.role_id,
                RoleAssignment.is_active == True
            )
        ).first()
        
        if existing_role:
            raise ValueError("Роль уже назначена пользователю")
        
        db_role_assignment = RoleAssignment(**role_assignment.dict(), assigned_by=assigned_by)
        db.add(db_role_assignment)
        db.commit()
        db.refresh(db_role_assignment)
        return db_role_assignment
    
    def get_user_roles(self, db: Session, user_id: int, active_only: bool = True) -> List[RoleAssignment]:
        """Получение ролей пользователя"""
        query = db.query(RoleAssignment).filter(RoleAssignment.user_id == user_id)
        if active_only:
            query = query.filter(RoleAssignment.is_active == True)
        return query.all()
    
    def get_role_assignment(self, db: Session, role_assignment_id: int) -> Optional[RoleAssignment]:
        """Получение конкретной связи пользователя с ролью"""
        return db.query(RoleAssignment).filter(RoleAssignment.id == role_assignment_id).first()
    
    def update_role_assignment(self, db: Session, role_assignment_id: int, role_assignment_update: RoleAssignmentUpdate) -> Optional[RoleAssignment]:
        """Обновление связи пользователя с ролью"""
        db_role_assignment = self.get_role_assignment(db, role_assignment_id)
        if not db_role_assignment:
            return None
        
        update_data = role_assignment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role_assignment, field, value)
        
        db.commit()
        db.refresh(db_role_assignment)
        return db_role_assignment
    
    def remove_role_from_user(self, db: Session, role_assignment_id: int) -> bool:
        """Удаление роли у пользователя (мягкое удаление)"""
        db_role_assignment = self.get_role_assignment(db, role_assignment_id)
        if not db_role_assignment:
            return False
        
        db_role_assignment.is_active = False
        db.commit()
        return True
    
    def get_users_by_role(self, db: Session, role_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение пользователей по роли"""
        return db.query(User).join(RoleAssignment).filter(
            and_(RoleAssignment.role_id == role_id, RoleAssignment.is_active == True)
        ).offset(skip).limit(limit).all()
    
    def get_user_roles_detailed(self, db: Session, user_id: int) -> List[dict]:
        """Получение детальной информации о ролях пользователя"""
        # Используем raw SQL для избежания проблем с связями
        result = db.execute("""
            SELECT ur.id, ur.user_id, ur.role_id, ur.assigned_by, ur.assigned_at, ur.expires_at, ur.is_active,
                   r.id as role_id, r.name as role_name, r.description as role_description, 
                   r.permissions as role_permissions, r.is_active as role_is_active,
                   r.created_at as role_created_at, r.updated_at as role_updated_at,
                   u.username as assigned_by_username
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            LEFT JOIN users u ON ur.assigned_by = u.id
            WHERE ur.user_id = :user_id
        """, {"user_id": user_id})
        
        detailed_roles = []
        for row in result:
            role = Role(
                id=row.role_id,
                name=row.role_name,
                description=row.role_description,
                permissions=row.role_permissions,
                is_active=row.role_is_active,
                created_at=row.role_created_at,
                updated_at=row.role_updated_at
            )
            
            role_assignment = RoleAssignment(
                id=row.id,
                user_id=row.user_id,
                role_id=row.role_id,
                assigned_by=row.assigned_by,
                assigned_at=row.assigned_at,
                expires_at=row.expires_at,
                is_active=row.is_active
            )
            
            detailed_roles.append({
                "role_assignment": role_assignment,
                "role": role,
                "assigned_by_username": row.assigned_by_username
            })
        
        return detailed_roles

# Создаем экземпляры для использования
role_crud = RoleCRUD()
role_assignment_crud = RoleAssignmentCRUD()
