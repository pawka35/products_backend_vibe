from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.models import User as UserModel, UserRole
from products.models import OrderStatus
from products.schemas import (
    Order as OrderSchema, 
    OrderSummary,
    ProductPurchase,
    OrderStatusUpdate
)
from auth.utils import get_current_active_user
from products.crud import (
    get_all_orders, 
    get_order, 
    get_orders_by_status,
    update_product_purchase_status,
    update_order_status,
    get_order_summary,
    check_order_completion
)

router = APIRouter(prefix="/executor", tags=["executor"])

def require_executor(current_user: UserModel = Depends(get_current_active_user)):
    """Проверка, что пользователь является исполнителем"""
    if current_user.role not in [UserRole.EXECUTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Требуются права исполнителя"
        )
    return current_user

@router.get("/orders", response_model=List[OrderSummary])
async def get_available_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение списка доступных заказов (только для исполнителей)
    """
    # Исполнители видят заказы со статусом PENDING и IN_PROGRESS
    orders = get_orders_by_status(db, OrderStatus.PENDING, skip, limit)
    orders.extend(get_orders_by_status(db, OrderStatus.IN_PROGRESS, skip, limit))
    
    order_summaries = []
    for order in orders:
        summary = get_order_summary(db, order.id)
        if summary:
            order_summaries.append(summary)
    
    return order_summaries

@router.get("/orders/{order_id}", response_model=OrderSchema)
async def get_order_details(
    order_id: int,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение деталей заказа (только для исполнителей)
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400, 
            detail="Можно работать только с активными заказами"
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
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
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
    
    # Проверяем, что заказ активен
    order = get_order(db, product.order_id)
    if not order or order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400, 
            detail="Можно работать только с активными заказами"
        )
    
    # Обновляем статус продукта
    updated_product = update_product_purchase_status(db, product_id, purchase_data, current_user.id)
    
    # Проверяем, можно ли завершить заказ
    if check_order_completion(db, product.order_id):
        update_order_status(db, product.order_id, OrderStatus.COMPLETED)
    
    # Возвращаем обновленный заказ
    return get_order(db, product.order_id)

@router.put("/orders/{order_id}/complete", response_model=OrderSchema)
async def complete_order(
    order_id: int,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Завершить заказ (только для исполнителей, если все продукты куплены)
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400, 
            detail="Можно завершить только активный заказ"
        )
    
    # Проверяем, что все продукты куплены
    if not check_order_completion(db, order_id):
        raise HTTPException(
            status_code=400, 
            detail="Нельзя завершить заказ, пока не все продукты куплены"
        )
    
    updated_order = update_order_status(db, order_id, OrderStatus.COMPLETED)
    return updated_order

@router.get("/orders/status/{status}", response_model=List[OrderSummary])
async def get_orders_by_status_executor(
    status: OrderStatus,
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_executor),
    db: Session = Depends(get_db)
):
    """
    Получение заказов по статусу (только для исполнителей)
    """
    orders = get_orders_by_status(db, status, skip, limit)
    
    order_summaries = []
    for order in orders:
        summary = get_order_summary(db, order.id)
        if summary:
            order_summaries.append(summary)
    
    return order_summaries
