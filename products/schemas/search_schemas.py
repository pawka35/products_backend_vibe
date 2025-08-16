from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class ProductSearchRequest(BaseModel):
    """Запрос на поиск товаров"""
    query: str
    page: Optional[int] = 1

class ExternalProduct(BaseModel):
    """Внешний товар из Maxi Retail"""
    id: Optional[Union[str, int]] = None
    name: str
    price: Optional[float] = None
    image: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    search_query: str
    source: str = "maxi-retail.ru"

    class Config:
        from_attributes = True

class ProductSearchResponse(BaseModel):
    """Ответ на поиск товаров"""
    query: str
    total_found: int
    total_pages: int
    current_page: int
    has_next: bool
    has_prev: bool
    products: List[ExternalProduct]
    search_timestamp: datetime
    source: str = "maxi-retail.ru"

    class Config:
        from_attributes = True

class PaginationInfo(BaseModel):
    """Информация о пагинации"""
    current_page: int
    total_pages: int
    total_items: int
    has_next: bool
    has_prev: bool
