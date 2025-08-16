from pydantic import BaseModel
from typing import Optional
from auth.models import UserRole
from auth.schemas import UserResponse

class ChangePasswordRequest(BaseModel):
    new_password: str

class ChangeRoleRequest(BaseModel):
    new_role: UserRole

class UserManagementResponse(BaseModel):
    message: str
    user: Optional[UserResponse] = None

class UserStatistics(BaseModel):
    total_users: int
    users_by_role: dict[str, int]

class BulkUserOperation(BaseModel):
    user_ids: list[int]
    operation: str  # "change_role", "deactivate", etc.
    new_role: Optional[UserRole] = None
