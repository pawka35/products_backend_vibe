from pydantic import BaseModel
from typing import Optional, List
from products.models import OrderStatus
from datetime import datetime

# Схемы для продуктов и заказов
class ProductBase(BaseModel):
    name: str
    quantity: int = 1
    notes: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None

class Product(ProductBase):
    id: int
    is_purchased: bool
    purchased_at: Optional[datetime] = None
    purchased_by: Optional[int] = None
    order_id: int

    class Config:
        from_attributes = True

class ProductPurchase(BaseModel):
    is_purchased: bool
    notes: Optional[str] = None

class OrderBase(BaseModel):
    pass

class OrderCreate(BaseModel):
    products: List[ProductCreate]

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None

class Order(OrderBase):
    id: int
    customer_id: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    products: List[Product]

    class Config:
        from_attributes = True

class OrderSummary(BaseModel):
    id: int
    customer_id: int
    status: OrderStatus
    created_at: datetime
    total_products: int
    purchased_products: int
    is_completable: bool

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: OrderStatus
