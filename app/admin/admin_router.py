from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from auth.models import User as UserModel, UserRole
from auth.schemas import UserResponse, UserList
from auth.utils import get_current_active_user
from auth.crud import get_users, get_user, get_users_by_role
from app.crud import (
    change_user_password,
    change_user_role,
    deactivate_user,
    get_user_statistics
)
from app.schemas import (
    ChangePasswordRequest,
    ChangeRoleRequest,
    UserManagementResponse,
    UserStatistics,
    BulkUserOperation
)
from products.crud import (
    get_all_orders_with_filters,
    get_orders_count_with_filters,
    get_order_summary
)
from products.schemas import (
    OrdersListResponse,
    OrderWithDetails
)
from products.models import OrderStatus

router = APIRouter(prefix="/admin", tags=["admin"])

def require_admin(current_user: UserModel = Depends(get_current_active_user)):
    """Проверка, что пользователь является администратором"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return current_user

@router.get("/users", response_model=List[UserList])
async def admin_get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение списка всех пользователей (только для администраторов)
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def admin_get_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение конкретного пользователя (только для администраторов)
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.put("/users/{user_id}/password", response_model=UserManagementResponse)
async def admin_change_user_password(
    user_id: int,
    password_data: ChangePasswordRequest,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Изменение пароля пользователя (только для администраторов)
    """
    updated_user = change_user_password(db, user_id, password_data.new_password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserManagementResponse(
        message="Пароль пользователя успешно изменен",
        user=updated_user
    )

@router.put("/users/{user_id}/role", response_model=UserManagementResponse)
async def admin_change_user_role(
    user_id: int,
    role_data: ChangeRoleRequest,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Изменение роли пользователя (только для администраторов)
    """
    updated_user = change_user_role(db, user_id, role_data.new_role)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserManagementResponse(
        message="Роль пользователя успешно изменена",
        user=updated_user
    )

@router.delete("/users/{user_id}", response_model=UserManagementResponse)
async def admin_deactivate_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Деактивация пользователя (только для администраторов)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя деактивировать самого себя"
        )
    
    result = deactivate_user(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return UserManagementResponse(
        message="Пользователь успешно деактивирован"
    )

@router.get("/users/role/{role}", response_model=List[UserList])
async def admin_get_users_by_role(
    role: UserRole,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение пользователей по роли (только для администраторов)
    """
    users = get_users_by_role(db, role)
    return users[skip:skip + limit]

@router.get("/statistics", response_model=UserStatistics)
async def admin_get_statistics(
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение статистики по пользователям (только для администраторов)
    """
    return get_user_statistics(db)

@router.post("/users/bulk/change-role", response_model=UserManagementResponse)
async def admin_bulk_change_role(
    bulk_data: BulkUserOperation,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Массовое изменение ролей пользователей (только для администраторов)
    """
    if bulk_data.operation == "change_role" and bulk_data.new_role:
        changed_count = 0
        for user_id in bulk_data.user_ids:
            if user_id != current_user.id:  # Нельзя изменить свою роль
                result = change_user_role(db, user_id, bulk_data.new_role)
                if result:
                    changed_count += 1
        
        return UserManagementResponse(
            message=f"Роли изменены для {changed_count} пользователей"
        )
    
    raise HTTPException(
        status_code=400, 
        detail="Неподдерживаемая операция"
    )

@router.get("/orders", response_model=OrdersListResponse)
async def admin_get_all_orders(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    executor_id: Optional[int] = Query(None, description="Фильтр по ID исполнителя"),
    customer_id: Optional[int] = Query(None, description="Фильтр по ID заказчика"),
    date_from: Optional[datetime] = Query(None, description="Фильтр по дате создания (от)"),
    date_to: Optional[datetime] = Query(None, description="Фильтр по дате создания (до)"),
    status: Optional[OrderStatus] = Query(
        None, 
        description="Фильтр по статусу заказа",
        enum=[OrderStatus.PENDING, OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED, OrderStatus.CANCELLED]
    ),
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Получение всех заказов с фильтрами (только для администраторов)
    
    Фильтры:
    - executor_id: Поиск заказов конкретного исполнителя
    - customer_id: Поиск заказов конкретного заказчика
    - date_from: Заказы созданные с указанной даты
    - date_to: Заказы созданные до указанной даты
    - status: Фильтр по статусу заказа (pending, in_progress, completed, cancelled)
    
    Поддерживается пагинация.
    """
    # Вычисляем offset для пагинации
    skip = (page - 1) * per_page
    
    # Получаем заказы с фильтрами
    orders = get_all_orders_with_filters(
        db=db,
        skip=skip,
        limit=per_page,
        executor_id=executor_id,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )
    
    # Получаем общее количество заказов с теми же фильтрами
    total_count = get_orders_count_with_filters(
        db=db,
        executor_id=executor_id,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )
    
    # Вычисляем пагинацию
    total_pages = (total_count + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    # Формируем детальную информацию о заказах
    orders_with_details = []
    for order in orders:
        # Получаем информацию о заказчике и исполнителе
        customer = get_user(db, order.customer_id)
        executor = get_user(db, order.executor_id)
        
        # Получаем сводку по заказу
        summary = get_order_summary(db, order.id)
        
        # Преобразуем продукты в словари
        products_data = []
        for product in order.products:
            product_dict = {
                "id": product.id,
                "name": product.name,
                "quantity": product.quantity,
                "notes": product.notes,
                "is_purchased": product.is_purchased,
                "purchased_at": product.purchased_at.isoformat() if product.purchased_at else None,
                "purchased_by": product.purchased_by,
                "order_id": product.order_id
            }
            products_data.append(product_dict)
        
        # Создаем детальную информацию о заказе
        order_detail = {
            "id": order.id,
            "customer_id": order.customer_id,
            "executor_id": order.executor_id,
            "status": order.status.value,  # Преобразуем enum в строку
            "created_at": order.created_at.isoformat() if order.created_at else None,  # Преобразуем datetime в строку
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "completed_at": order.completed_at.isoformat() if order.completed_at else None,
            "products": products_data,
            "customer_username": customer.username if customer else None,
            "executor_username": executor.username if executor else None,
            "total_products": summary["total_products"] if summary else 0,
            "purchased_products": summary["purchased_products"] if summary else 0,
            "is_completable": summary["is_completable"] if summary else False
        }
        orders_with_details.append(order_detail)
    
    return OrdersListResponse(
        orders=orders_with_details,
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
