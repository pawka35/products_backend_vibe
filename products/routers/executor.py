from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
from database import get_db
from auth.models import User as UserModel, UserRole
from products.models import OrderStatus
from products.schemas import (
    Order as OrderSchema, 
    OrderSummary,
    ProductPurchase,
    OrderStatusUpdate,
    OrderComplete,
    ExecutorOrdersListResponse,
    OrderStatusStatistics,
    OrderStatusCount
)
from auth.utils import get_current_active_user
from auth.utils.role_utils import has_executor_access
from products.crud import (
    get_all_orders, 
    get_order, 
    get_orders_by_status,
    update_product_purchase_status,
    update_order_status,
    get_order_summary,
    check_order_completion,
    get_executor_orders_with_filters,
    get_executor_orders_count_with_filters,
    get_executor_orders_count_by_status
)
from auth.crud import get_users_by_role
from auth.schemas import UserList

router = APIRouter(prefix="/api/executor", tags=["executor"])

def require_executor(current_user: UserModel = Depends(get_current_active_user)):
    """
    Проверка, что пользователь является исполнителем.
    Поддерживает множественные роли - пользователь может иметь роль executor
    или быть администратором (admin имеет доступ ко всем функциям).
    """
    if not has_executor_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Требуются права исполнителя"
        )
    return current_user

@router.get("/orders", response_model=ExecutorOrdersListResponse)
async def get_available_orders(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    customer_id: Optional[int] = Query(None, description="Фильтр по ID заказчика"),
    date_from: Optional[datetime] = Query(None, description="Фильтр по дате создания (от)"),
    date_to: Optional[datetime] = Query(None, description="Фильтр по дате создания (до)"),
    status: Optional[OrderStatus] = Query(
        None, 
        description="Фильтр по статусу заказа",
        enum=[OrderStatus.PENDING, OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED, OrderStatus.CANCELLED]
    ),
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение списка заказов исполнителя с фильтрами (только для исполнителей и администраторов)
    
    Администратор видит только заказы, где он назначен исполнителем.
    
    Фильтры:
    - customer_id: Поиск заказов конкретного заказчика
    - date_from: Заказы созданные с указанной даты
    - date_to: Заказы созданные до указанной даты
    - status: Фильтр по статусу заказа (pending, in_progress, completed, cancelled)
    
    Поддерживается пагинация.
    """
    # Вычисляем offset для пагинации
    skip = (page - 1) * per_page
    
    # Получаем заказы исполнителя с фильтрами
    orders = get_executor_orders_with_filters(
        db=db,
        executor_id=current_user.id,  # Используем ID текущего пользователя как исполнителя
        skip=skip,
        limit=per_page,
        customer_id=customer_id,
        date_from=date_from,
        date_to=date_to,
        status=status
    )
    
    # Получаем общее количество заказов исполнителя с теми же фильтрами
    total_count = get_executor_orders_count_with_filters(
        db=db,
        executor_id=current_user.id,
        customer_id=customer_id,
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
    
    return ExecutorOrdersListResponse(
        orders=order_summaries,
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@router.get("/orders/{order_id}", response_model=OrderSchema)
async def get_order_details(
    order_id: int,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение деталей заказа (только для исполнителей)
    
    Исполнитель может просматривать заказы в любом статусе, 
    но только те, где он назначен исполнителем.
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что текущий пользователь назначен исполнителем этого заказа
    if order.executor_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ запрещен. Вы не назначены исполнителем этого заказа"
        )
    
    return order

@router.get("/orders/{order_id}/summary", response_model=OrderSummary)
async def get_order_summary_executor(
    order_id: int,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение сводки по заказу (только для исполнителей)
    
    Исполнитель может просматривать сводки заказов в любом статусе, 
    но только тех, где он назначен исполнителем.
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что текущий пользователь назначен исполнителем этого заказа
    if order.executor_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ запрещен. Вы не назначены исполнителем этого заказа"
        )
    
    summary = get_order_summary(db, order_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Сводка не найдена")
    
    return summary

@router.put("/orders/{order_id}/start", response_model=OrderSchema)
async def start_order_execution(
    order_id: int,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Начать исполнение заказа (только для исполнителей)
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что текущий пользователь назначен исполнителем этого заказа
    if order.executor_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ запрещен. Вы не назначены исполнителем этого заказа"
        )
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail="Можно начать только ожидающий заказ"
        )
    
    updated_order = update_order_status(db, order_id, OrderStatus.IN_PROGRESS)
    return updated_order

@router.put("/products/{product_id}/purchase", response_model=OrderSchema)
async def mark_product_purchased(
    product_id: int,
    purchase_data: ProductPurchase,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Отметить продукт как купленный (только для исполнителей)
    """
    from products.crud import get_product
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Проверяем, что заказ активен и исполнитель имеет доступ
    order = get_order(db, product.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что текущий пользователь назначен исполнителем этого заказа
    if order.executor_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ запрещен. Вы не назначены исполнителем этого заказа"
        )
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400, 
            detail="Можно работать только с активными заказами"
        )
    
    # Обновляем статус продукта
    updated_product = update_product_purchase_status(db, product_id, purchase_data, current_user.id)
    
    # Возвращаем обновленный заказ
    return get_order(db, product.order_id)

@router.put("/products/{product_id}/unpurchase", response_model=OrderSchema)
async def unmark_product_purchased(
    product_id: int,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Снять пометку "куплен" с продукта (только для исполнителей)
    """
    from products.crud import get_product
    
    product = get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    
    # Проверяем, что заказ активен и исполнитель имеет доступ
    order = get_order(db, product.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что текущий пользователь назначен исполнителем этого заказа
    if order.executor_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ запрещен. Вы не назначены исполнителем этого заказа"
        )
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400, 
            detail="Можно работать только с активными заказами"
        )
    
    # Создаем данные для снятия пометки
    unpurchase_data = ProductPurchase(
        is_purchased=False,
        notes="Пометка 'куплен' снята"
    )
    
    # Обновляем статус продукта
    updated_product = update_product_purchase_status(db, product_id, unpurchase_data, current_user.id)
    
    # Возвращаем обновленный заказ
    return get_order(db, product.order_id)

@router.put("/orders/{order_id}/complete", response_model=OrderSchema)
async def complete_order(
    order_id: int,
    complete_data: OrderComplete = None,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Завершить заказ (только для исполнителей)
    
    Правила завершения:
    - Если ВСЕ продукты куплены → можно завершить без комментария
    - Если НЕ все продукты куплены → обязательно нужен комментарий с объяснением
    
    Параметры:
    - **order_id**: ID заказа
    - **complete_comment**: Комментарий исполнителя о выполнении заказа
      - Необязателен, если все продукты куплены
      - ОБЯЗАТЕЛЕН, если не все продукты куплены
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Проверяем, что текущий пользователь назначен исполнителем этого заказа
    if order.executor_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ запрещен. Вы не назначены исполнителем этого заказа"
        )
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400, 
            detail="Можно завершить только активный заказ"
        )
    
    # Получаем комментарий из тела запроса, если он передан
    complete_comment = complete_data.complete_comment if complete_data else None
    
    # Проверяем, все ли продукты куплены
    all_products_purchased = check_order_completion(db, order_id)
    
    # Если НЕ все продукты куплены, то комментарий ОБЯЗАТЕЛЕН
    if not all_products_purchased:
        if not complete_comment or not complete_comment.strip():
            raise HTTPException(
                status_code=400, 
                detail="Невозможно завершить заказ, если не все продукты куплены. "
                       "Необходимо указать комментарий с объяснением причины."
            )
    
    # Завершаем заказ (с комментарием или без, в зависимости от ситуации)
    updated_order = update_order_status(db, order_id, OrderStatus.COMPLETED, complete_comment)
    return updated_order

@router.get("/orders/statistics/by-status", response_model=Dict[str, int])
async def get_orders_statistics_by_status(
    status: Optional[OrderStatus] = Query(
        None,
        description="Опциональный фильтр по статусу. Если указан, возвращается только количество заказов в этом статусе."
    ),
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение статистики заказов по статусам (только для исполнителей)
    
    Возвращает словарь, где ключ - статус заявки, значение - количество заявок в таком статусе.
    
    Статусы:
    - pending: Ожидает исполнения
    - in_progress: В процессе исполнения
    - completed: Исполнен
    - cancelled: Отменен
    
    Если передан параметр `status`, возвращается только количество заказов в указанном статусе.
    """
    status_counts = get_executor_orders_count_by_status(db, current_user.id, status)
    
    # Преобразуем словарь с OrderStatus ключами в словарь со строковыми ключами
    result = {
        stat.value: count
        for stat, count in status_counts.items()
    }
    
    return result

@router.get("/customers", response_model=List[UserList])
async def get_customers_list(
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение списка всех заказчиков (только для исполнителей)
    
    Возвращает список активных пользователей с ролью customer.
    Используется для фильтрации заказов по заказчику.
    """
    # Получаем всех пользователей с ролью customer
    customers = get_users_by_role(db, UserRole.CUSTOMER)
    
    # Фильтруем только активных пользователей
    active_customers = [customer for customer in customers if customer.is_active]
    
    return active_customers
