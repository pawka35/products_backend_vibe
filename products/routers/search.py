from fastapi import APIRouter, Depends, HTTPException
from auth.models import User as UserModel
from auth.utils import get_current_active_user
from products.schemas import ProductSearchRequest, ProductSearchResponse, PaginationInfo
from products.services import MaxiRetailSearchService
from datetime import datetime

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/products", response_model=ProductSearchResponse)
async def search_products(
    search_request: ProductSearchRequest,
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Поиск товаров на Maxi Retail с пагинацией
    
    - **query**: Поисковый запрос
    - **page**: Номер страницы (по умолчанию 1)
    """
    try:
        # Поиск товаров через сервис с пагинацией
        async with MaxiRetailSearchService() as search_service:
            products, pagination_info = await search_service.search_products(
                search_request.query,
                search_request.page,
            )
        
        # Создаем ответ с информацией о пагинации
        response = ProductSearchResponse(
            query=search_request.query,
            total_found=pagination_info["total_items"],
            total_pages=pagination_info["total_pages"],
            current_page=pagination_info["current_page"],
            has_next=pagination_info["has_next"],
            has_prev=pagination_info["has_prev"],
            products=products,
            search_timestamp=datetime.now(),
            source="maxi-retail.ru"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске товаров: {str(e)}"
        )
