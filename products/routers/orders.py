from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.models import User as UserModel, UserRole
from products.models import OrderStatus
from products.schemas import (
    OrderCreate, 
    Order as OrderSchema, 
    OrderSummary,
    OrderStatusUpdate
)
from auth.utils import get_current_active_user
from products.crud import (
    create_order, 
    get_user_orders, 
    get_order, 
    update_order_status,
    get_order_summary
)

router = APIRouter(prefix="/orders", tags=["orders"])

def require_customer(current_user: UserModel = Depends(get_current_active_user)):
    """Проверка, что пользователь является заказчиком"""
    if current_user.role not in [UserRole.CUSTOMER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Требуются права заказчика"
        )
    return current_user

@router.post("/", response_model=OrderSchema)
async def create_new_order(
    order: OrderCreate,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Создание нового заказа (только для заказчиков)
    """
    if not order.products:
        raise HTTPException(
            status_code=400, 
            detail="Заказ должен содержать хотя бы один продукт"
        )
    
    db_order = create_order(db, order, current_user.id)
    return db_order

@router.get("/", response_model=List[OrderSummary])
async def get_my_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение списка заказов текущего пользователя (только для заказчиков)
    """
    orders = get_user_orders(db, current_user.id, skip=skip, limit=limit)
    order_summaries = []
    
    for order in orders:
        summary = get_order_summary(db, order.id)
        if summary:
            order_summaries.append(summary)
    
    return order_summaries

@router.get("/{order_id}", response_model=OrderSchema)
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

@router.get("/{order_id}/summary", response_model=OrderSummary)
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

@router.put("/{order_id}/cancel", response_model=OrderSchema)
async def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Отмена заказа (только для заказчиков, только свои заказы)
    """
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Доступ только к своим заказам"
        )
    
    if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=400, 
            detail="Нельзя отменить завершенный или отмененный заказ"
        )
    
    updated_order = update_order_status(db, order_id, OrderStatus.CANCELLED)
    return updated_order
