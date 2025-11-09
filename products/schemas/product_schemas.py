from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_purchased: bool
    purchased_at: Optional[datetime] = None
    purchased_by: Optional[int] = None
    order_id: int

class ProductPurchase(BaseModel):
    is_purchased: bool
    notes: Optional[str] = None

class OrderBase(BaseModel):
    pass

class OrderCreate(BaseModel):
    products: List[ProductCreate]
    executor_id: int  # Обязательный ID исполнителя

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None

class OrderComplete(BaseModel):
    """Схема для завершения заказа с необязательным комментарием"""
    complete_comment: Optional[str] = None

class Order(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_id: int
    executor_id: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    complete_comment: Optional[str] = None
    products: List[Product]

class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_id: int
    executor_id: int
    status: OrderStatus
    created_at: datetime
    total_products: int
    purchased_products: int
    is_completable: bool

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class OrderEdit(BaseModel):
    """Схема для редактирования заказа заказчиком"""
    products: Optional[List[ProductCreate]] = None
    executor_id: Optional[int] = None

# Схемы для административных операций с заказами
class OrderFilters(BaseModel):
    """Схема фильтров для поиска заказов"""
    executor_id: Optional[int] = None
    customer_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[OrderStatus] = None

class OrderWithDetails(BaseModel):
    """Расширенная схема заказа с деталями для администратора"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    customer_id: int
    executor_id: int
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    products: List[Product]
    # Дополнительная информация
    customer_username: Optional[str] = None
    executor_username: Optional[str] = None
    total_products: int
    purchased_products: int
    is_completable: bool

class OrdersListResponse(BaseModel):
    """Схема ответа со списком заказов и пагинацией"""
    orders: List[dict]  # Используем dict вместо OrderWithDetails для гибкости
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class UserOrdersListResponse(BaseModel):
    """Схема ответа со списком заказов пользователя и пагинацией"""
    orders: List[OrderSummary]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ExecutorOrdersListResponse(BaseModel):
    """Схема ответа со списком заказов исполнителя и пагинацией"""
    orders: List[OrderSummary]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

# Схемы для сохраненных товаров
class SavedProductCreate(BaseModel):
    """Схема для создания сохраненного товара"""
    name: str
    quantity: int = 1
    notes: Optional[str] = None

class SavedProductUpdate(BaseModel):
    """Схема для обновления сохраненного товара"""
    name: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None

class SavedProduct(BaseModel):
    """Схема сохраненного товара"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    quantity: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class SavedProductListResponse(BaseModel):
    """Схема ответа со списком сохраненных товаров"""
    products: List[SavedProduct]
    total_count: int
