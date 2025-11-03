from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum
from typing import List, Set

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    EXECUTOR = "executor"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)  # Оставляем для обратной совместимости
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    orders = relationship("Order", foreign_keys="Order.customer_id", back_populates="customer")
    search_history = relationship("SearchHistory", back_populates="user")
    
    # Связь с множественными ролями
    role_assignments = relationship("RoleAssignment", foreign_keys="[RoleAssignment.user_id]", back_populates="user", cascade="all, delete-orphan")
    
    def get_roles(self) -> Set[str]:
        """
        Получить все активные роли пользователя.
        Возвращает set из названий ролей.
        """
        if not self.role_assignments:
            # Если нет назначенных ролей, используем основную роль из поля role
            return {self.role.value}
        
        # Получаем все активные роли из role_assignments
        active_roles = set()
        for assignment in self.role_assignments:
            if assignment.is_active:
                # Проверяем срок действия роли
                if assignment.expires_at is None or assignment.expires_at > func.now():
                    if hasattr(assignment, 'role') and assignment.role:
                        active_roles.add(assignment.role.name)
        
        # Если нет активных назначенных ролей, возвращаем основную роль
        if not active_roles:
            return {self.role.value}
        
        return active_roles
    
    def has_role(self, role_name: str) -> bool:
        """
        Проверить, имеет ли пользователь указанную роль.
        """
        roles = self.get_roles()
        return role_name in roles or role_name.lower() in roles
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """
        Проверить, имеет ли пользователь хотя бы одну из указанных ролей.
        """
        user_roles = self.get_roles()
        return any(role in user_roles or role.lower() in user_roles for role in role_names)
    
    def is_admin(self) -> bool:
        """
        Проверить, является ли пользователь администратором.
        """
        return self.has_role("admin") or self.role == UserRole.ADMIN
    
    def is_customer(self) -> bool:
        """
        Проверить, является ли пользователь заказчиком.
        """
        return self.has_role("customer") or self.role == UserRole.CUSTOMER
    
    def is_executor(self) -> bool:
        """
        Проверить, является ли пользователь исполнителем.
        """
        return self.has_role("executor") or self.role == UserRole.EXECUTOR
    
    def __repr__(self):
        roles = self.get_roles() if hasattr(self, 'role_assignments') else {self.role.value}
        return f"<User(id={self.id}, username='{self.username}', roles={roles})>"
