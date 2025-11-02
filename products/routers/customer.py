from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from auth.models import User as UserModel, UserRole
from products.models import OrderStatus
from products.schemas import (
    OrderCreate, 
    Order as OrderSchema, 
    OrderSummary,
    OrderStatusUpdate,
    UserOrdersListResponse,
    OrderEdit
)
from auth.utils import get_current_active_user
from products.crud import (
    create_order, 
    get_user_orders, 
    get_order, 
    update_order_status,
    get_order_summary,
    get_user_orders_with_filters,
    get_user_orders_count_with_filters,
    update_order,
    copy_order
)
from auth.crud import get_user, get_users_by_role
from auth.schemas import UserList

router = APIRouter(prefix="/customer", tags=["customer"])

def require_customer(current_user: UserModel = Depends(get_current_active_user)):
    """Проверка, что пользователь является заказчиком"""
    if current_user.role not in [UserRole.CUSTOMER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Требуются права заказчика"
        )
    return current_user

@router.post("/orders", response_model=OrderSchema)
async def create_new_order(
    order: OrderCreate,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Создание нового заказа (только для заказчиков)
    Требует обязательного указания исполнителя с ролью EXECUTOR
    """
    if not order.products:
        raise HTTPException(
            status_code=400, 
            detail="Заказ должен содержать хотя бы один продукт"
        )
    
    # Проверяем, что указанный исполнитель существует и имеет роль EXECUTOR
    executor = get_user(db, order.executor_id)
    if not executor:
        raise HTTPException(
            status_code=404,
            detail="Исполнитель не найден"
        )
    
    if executor.role != UserRole.EXECUTOR:
        raise HTTPException(
            status_code=400,
            detail="Указанный пользователь не является исполнителем"
        )
    
    if not executor.is_active:
        raise HTTPException(
            status_code=400,
            detail="Указанный исполнитель неактивен"
        )
    
    # Проверяем, что заказчик не назначает заказ самому себе
    if order.executor_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя назначить заказ самому себе"
        )
    
    db_order = create_order(db, order, current_user.id)
    return db_order

@router.get("/orders/executors", response_model=List[UserList])
async def get_available_executors(
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение списка доступных исполнителей (только для заказчиков)
    """
    executors = get_users_by_role(db, UserRole.EXECUTOR)
    active_executors = [executor for executor in executors if executor.is_active]
    return active_executors

@router.get("/orders", response_model=UserOrdersListResponse)
async def get_my_orders(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    executor_id: Optional[int] = Query(None, description="Фильтр по ID исполнителя"),
    date_from: Optional[datetime] = Query(None, description="Фильтр по дате создания (от)"),
    date_to: Optional[datetime] = Query(None, description="Фильтр по дате создания (до)"),
    status: Optional[OrderStatus] = Query(
        None, 
        description="Фильтр по статусу заказа",
        enum=[OrderStatus.PENDING, OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED, OrderStatus.CANCELLED]
    ),
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение списка заказов текущего пользователя с фильтрами (только для заказчиков)
    
    Фильтры:
    - executor_id: Поиск заказов конкретного исполнителя
    - date_from: Заказы созданные с указанной даты
    - date_to: Заказы созданные до указанной даты
    - status: Фильтр по статусу заказа (pending, in_progress, completed, cancelled)
    
    Поддерживается пагинация.
    """
    # Вычисляем offset для пагинации
    skip = (page - 1) * per_page
    
    # Получаем заказы пользователя с фильтрами
    orders = get_user_orders_with_filters(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=per_page,
        executor_id=executor_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )
    
    # Получаем общее количество заказов пользователя с теми же фильтрами
    total_count = get_user_orders_count_with_filters(
        db=db,
        user_id=current_user.id,
        executor_id=executor_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )
    
    # Вычисляем пагинацию
    total_pages = (total_count + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1
    
    # Формируем сводки по заказам
    order_summaries = []
    for order in orders:
        summary = get_order_summary(db, order.id)
        if summary:
            order_summaries.append(summary)
    
    return UserOrdersListResponse(
        orders=order_summaries,
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/orders/{order_id}", response_model=OrderSchema)
async def get_my_order(
    order_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение конкретного заказа (только для заказчиков, только свои заказы)
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ только к своим заказам"
        )
    
    return order

@router.get("/orders/{order_id}/summary", response_model=OrderSummary)
async def get_order_summary_endpoint(
    order_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение сводки по заказу (только для заказчиков, только свои заказы)
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ только к своим заказам"
        )
    
    summary = get_order_summary(db, order_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Сводка не найдена")
    
    return summary

@router.put("/orders/{order_id}", response_model=OrderSchema)
async def edit_order(
    order_id: int,
    order_edit: OrderEdit,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Редактирование заказа (только для заказчиков, только свои заказы)
    
    Можно редактировать только заказы со статусом PENDING (новые заказы).
    Заказы в работе (IN_PROGRESS), выполненные (COMPLETED) и отмененные (CANCELLED) 
    редактировать нельзя.
    
    Можно изменить:
    - Исполнителя (executor_id)
    - Список продуктов (products)
    
    При обновлении продуктов все старые продукты удаляются и создаются новые.
    """
    # Проверяем, что заказ существует
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что заказ принадлежит текущему пользователю
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ только к своим заказам"
        )
    
    # Проверяем, что заказ можно редактировать (только PENDING)
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Редактировать можно только новые заказы (статус: pending). Текущий статус: {order.status.value}"
        )
    
    # Проверяем, что указано хотя бы одно поле для изменения
    if order_edit.executor_id is None and order_edit.products is None:
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать хотя бы одно поле для изменения (executor_id или products)"
        )
    
    # Если указан новый исполнитель, проверяем его
    if order_edit.executor_id is not None:
        executor = get_user(db, order_edit.executor_id)
        if not executor:
            raise HTTPException(
                status_code=404,
                detail="Исполнитель не найден"
            )
        
        if executor.role != UserRole.EXECUTOR:
            raise HTTPException(
                status_code=400,
                detail="Указанный пользователь не является исполнителем"
            )
        
        if not executor.is_active:
            raise HTTPException(
                status_code=400,
                detail="Указанный исполнитель неактивен"
            )
        
        # Проверяем, что заказчик не назначает заказ самому себе
        if order_edit.executor_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Нельзя назначить заказ самому себе"
            )
    
    # Если указаны продукты, проверяем, что список не пустой
    if order_edit.products is not None:
        if not order_edit.products:
            raise HTTPException(
                status_code=400,
                detail="Заказ должен содержать хотя бы один продукт"
            )
    
    # Обновляем заказ
    updated_order = update_order(db, order_id, order_edit)
    if not updated_order:
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении заказа"
        )
    
    return updated_order

@router.post("/orders/{order_id}/copy", response_model=OrderSchema)
async def copy_order_endpoint(
    order_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Копирование заказа (только для заказчиков, только свои заказы)
    
    Создает новый заказ на основе существующего с:
    - Тем же исполнителем
    - Теми же продуктами (все продукты со статусом "не куплен")
    - Статусом PENDING (новый заказ)
    
    Можно копировать только заказы, которые НЕ находятся в статусе PENDING (новый).
    То есть можно копировать заказы в статусах: IN_PROGRESS, COMPLETED, CANCELLED.
    """
    # Проверяем, что заказ существует
    original_order = get_order(db, order_id)
    if not original_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что заказ принадлежит текущему пользователю
    if original_order.customer_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ только к своим заказам"
        )
    
    # Проверяем, что заказ не в статусе PENDING (новый)
    if original_order.status == OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Нельзя копировать новый заказ (статус: pending). Копировать можно только заказы, которые были взяты в работу, выполнены или отменены."
        )
    
    # Копируем заказ
    copied_order = copy_order(db, order_id, current_user.id)
    if not copied_order:
        raise HTTPException(
            status_code=500,
            detail="Ошибка при копировании заказа"
        )
    
    return copied_order
