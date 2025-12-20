from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
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
    OrderEdit,
    SavedProductCreate,
    SavedProductUpdate,
    SavedProduct,
    SavedProductListResponse,
    ProductSearchRequest,
    ProductSearchResponse,
    OrderStatusStatistics,
    OrderStatusCount
)
from auth.utils import get_current_active_user
from auth.utils.role_utils import has_customer_access
from products.crud import (
    create_order, 
    get_user_orders, 
    get_order, 
    update_order_status,
    get_order_summary,
    get_user_orders_with_filters,
    get_user_orders_count_with_filters,
    update_order,
    copy_order,
    create_saved_product,
    get_saved_product,
    get_user_saved_products,
    get_user_saved_products_count,
    update_saved_product,
    delete_saved_product,
    get_user_orders_count_by_status
)
from auth.crud import get_user, get_users_by_role
from auth.schemas import UserList
from products.services import MaxiRetailSearchService

router = APIRouter(prefix="/api/customer", tags=["customer"])

def require_customer(current_user: UserModel = Depends(get_current_active_user)):
    """
    Проверка, что пользователь является заказчиком.
    Поддерживает множественные роли - пользователь может иметь роль customer
    или быть администратором (admin имеет доступ ко всем функциям).
    """
    if not has_customer_access(current_user):
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

@router.get("/orders/statistics/by-status", response_model=Dict[str, int])
async def get_orders_statistics_by_status(
    status: Optional[OrderStatus] = Query(
        None,
        description="Опциональный фильтр по статусу. Если указан, возвращается только количество заказов в этом статусе."
    ),
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение статистики заказов по статусам (только для заказчиков)
    
    Возвращает словарь, где ключ - статус заявки, значение - количество заявок в таком статусе.
    
    Статусы:
    - pending: Ожидает исполнения
    - in_progress: В процессе исполнения
    - completed: Исполнен
    - cancelled: Отменен
    
    Если передан параметр `status`, возвращается только количество заказов в указанном статусе.
    """
    status_counts = get_user_orders_count_by_status(db, current_user.id, status)
    
    # Преобразуем словарь с OrderStatus ключами в словарь со строковыми ключами
    result = {
        stat.value: count
        for stat, count in status_counts.items()
    }
    
    return result

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

@router.post("/orders/{order_id}/cancel", response_model=OrderSchema)
async def cancel_order_endpoint(
    order_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Отмена заказа (только для заказчиков, только свои заказы)
    
    Отменить можно только заказы со статусом PENDING (новые заказы, которые еще не взяты в работу).
    Заказы, которые уже в работе (IN_PROGRESS), выполнены (COMPLETED) 
    или уже отменены (CANCELLED), отменить нельзя.
    
    При отмене заказ переводится в статус CANCELLED.
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
    
    # Проверяем, что заказ можно отменить (только PENDING)
    if order.status != OrderStatus.PENDING:
        status_messages = {
            OrderStatus.IN_PROGRESS: "Заказ уже взят в работу и не может быть отменен",
            OrderStatus.COMPLETED: "Заказ уже выполнен и не может быть отменен",
            OrderStatus.CANCELLED: "Заказ уже отменен"
        }
        detail_message = status_messages.get(
            order.status, 
            f"Заказ в статусе '{order.status.value}' не может быть отменен"
        )
        raise HTTPException(
            status_code=400,
            detail=detail_message
        )
    
    # Отменяем заказ - меняем статус на CANCELLED
    cancelled_order = update_order_status(db, order_id, OrderStatus.CANCELLED)
    
    if not cancelled_order:
        raise HTTPException(
            status_code=500,
            detail="Ошибка при отмене заказа"
        )
    
    return cancelled_order

# Эндпоинты для сохраненных товаров
@router.post("/products/saved", response_model=SavedProduct)
async def create_saved_product_endpoint(
    saved_product: SavedProductCreate,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Создание сохраненного товара (только для заказчиков)
    """
    db_saved_product = create_saved_product(db, saved_product, current_user.id)
    return db_saved_product

@router.get("/products/saved", response_model=SavedProductListResponse)
async def get_saved_products_endpoint(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Количество записей на странице"),
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение списка сохраненных товаров текущего пользователя (только для заказчиков)
    
    Поддерживается пагинация.
    """
    # Вычисляем offset для пагинации
    skip = (page - 1) * per_page
    
    # Получаем сохраненные товары пользователя
    saved_products = get_user_saved_products(db, current_user.id, skip=skip, limit=per_page)
    
    # Получаем общее количество сохраненных товаров
    total_count = get_user_saved_products_count(db, current_user.id)
    
    return SavedProductListResponse(
        products=saved_products,
        total_count=total_count
    )

@router.get("/products/saved/{saved_product_id}", response_model=SavedProduct)
async def get_saved_product_endpoint(
    saved_product_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Получение конкретного сохраненного товара (только для заказчиков, только свои товары)
    """
    saved_product = get_saved_product(db, saved_product_id, current_user.id)
    if not saved_product:
        raise HTTPException(status_code=404, detail="Сохраненный товар не найден")
    
    return saved_product

@router.put("/products/saved/{saved_product_id}", response_model=SavedProduct)
async def update_saved_product_endpoint(
    saved_product_id: int,
    saved_product_update: SavedProductUpdate,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Обновление сохраненного товара (только для заказчиков, только свои товары)
    """
    updated_product = update_saved_product(db, saved_product_id, saved_product_update, current_user.id)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Сохраненный товар не найден")
    
    return updated_product

@router.delete("/products/saved/{saved_product_id}")
async def delete_saved_product_endpoint(
    saved_product_id: int,
    current_user: UserModel = Depends(require_customer),
    db: Session = Depends(get_db)
):
    """
    Удаление сохраненного товара (только для заказчиков, только свои товары)
    """
    success = delete_saved_product(db, saved_product_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Сохраненный товар не найден")
    
    return {"message": "Сохраненный товар успешно удален"}

# Эндпоинт для поиска товаров
@router.post("/search/products", response_model=ProductSearchResponse)
async def search_products(
    search_request: ProductSearchRequest,
    current_user: UserModel = Depends(require_customer)
):
    """
    Поиск товаров на Maxi Retail с пагинацией (только для заказчиков)
    
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
