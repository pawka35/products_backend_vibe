from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from products.models import Product, Order, OrderStatus, SavedProduct
from products.schemas import ProductCreate, OrderCreate, ProductPurchase, OrderEdit, SavedProductCreate, SavedProductUpdate
from datetime import datetime
from typing import Optional, List, Dict

# CRUD операции для заказов
def create_order(db: Session, order: OrderCreate, customer_id: int):
    """Создание нового заказа с обязательным исполнителем"""
    db_order = Order(
        customer_id=customer_id,
        executor_id=order.executor_id
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Создаем продукты для заказа
    for product_data in order.products:
        db_product = Product(
            name=product_data.name,
            quantity=product_data.quantity,
            notes=product_data.notes,
            order_id=db_order.id
        )
        db.add(db_product)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def get_order(db: Session, order_id: int):
    """Получение заказа по ID"""
    return db.query(Order).filter(Order.id == order_id).first()

def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Получение заказов пользователя (как заказчика)"""
    return db.query(Order).filter(Order.customer_id == user_id).offset(skip).limit(limit).all()

def get_user_orders_with_filters(
    db: Session, 
    user_id: int,
    skip: int = 0, 
    limit: int = 100,
    executor_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение заказов пользователя с фильтрами (для заказчиков)
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя (заказчика)
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        executor_id: Фильтр по ID исполнителя
        date_from: Фильтр по дате создания (от)
        date_to: Фильтр по дате создания (до)
        status: Фильтр по статусу заказа
    
    Returns:
        Список заказов пользователя с примененными фильтрами
    """
    query = db.query(Order).filter(Order.customer_id == user_id)
    
    # Применяем фильтры
    if executor_id is not None:
        query = query.filter(Order.executor_id == executor_id)
    
    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)
    
    if status is not None:
        query = query.filter(Order.status == status)
    
    # Сортируем по дате создания (новые сначала)
    query = query.order_by(desc(Order.created_at))
    
    return query.offset(skip).limit(limit).all()

def get_user_orders_count_with_filters(
    db: Session,
    user_id: int,
    executor_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение количества заказов пользователя с фильтрами (для пагинации)
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя (заказчика)
        executor_id: Фильтр по ID исполнителя
        date_from: Фильтр по дате создания (от)
        date_to: Фильтр по дате создания (до)
        status: Фильтр по статусу заказа
    
    Returns:
        Количество заказов пользователя с примененными фильтрами
    """
    query = db.query(Order).filter(Order.customer_id == user_id)
    
    # Применяем фильтры
    if executor_id is not None:
        query = query.filter(Order.executor_id == executor_id)
    
    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)
    
    if status is not None:
        query = query.filter(Order.status == status)
    
    return query.count()

def get_all_orders_with_users_and_filters(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    executor_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение всех заказов с фильтрами и предзагруженными пользователями (оптимизированная версия)
    """
    from auth.models import User
    
    query = db.query(Order).options(
        joinedload(Order.customer),
        joinedload(Order.executor),
        joinedload(Order.products)
    )

    # Применяем фильтры
    if executor_id is not None:
        query = query.filter(Order.executor_id == executor_id)

    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)

    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)

    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)

    if status is not None:
        query = query.filter(Order.status == status)

    # Сортируем по дате создания (новые сначала)
    query = query.order_by(desc(Order.created_at))

    return query.offset(skip).limit(limit).all()

def get_executor_orders(db: Session, executor_id: int, skip: int = 0, limit: int = 100):
    """Получение заказов исполнителя"""
    return db.query(Order).filter(Order.executor_id == executor_id).offset(skip).limit(limit).all()

def get_executor_orders_with_filters(
    db: Session, 
    executor_id: int,
    skip: int = 0, 
    limit: int = 100,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение заказов исполнителя с фильтрами
    
    Args:
        db: Сессия базы данных
        executor_id: ID исполнителя
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        customer_id: Фильтр по ID заказчика
        date_from: Фильтр по дате создания (от)
        date_to: Фильтр по дате создания (до)
        status: Фильтр по статусу заказа
    
    Returns:
        Список заказов исполнителя с примененными фильтрами
    """
    query = db.query(Order).filter(Order.executor_id == executor_id)
    
    # Применяем фильтры
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    
    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)
    
    if status is not None:
        query = query.filter(Order.status == status)
    
    # Сортируем по дате создания (новые сначала)
    query = query.order_by(desc(Order.created_at))
    
    return query.offset(skip).limit(limit).all()

def get_executor_orders_count_with_filters(
    db: Session,
    executor_id: int,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение количества заказов исполнителя с фильтрами (для пагинации)
    
    Args:
        db: Сессия базы данных
        executor_id: ID исполнителя
        customer_id: Фильтр по ID заказчика
        date_from: Фильтр по дате создания (от)
        date_to: Фильтр по дате создания (до)
        status: Фильтр по статусу заказа
    
    Returns:
        Количество заказов исполнителя с примененными фильтрами
    """
    query = db.query(Order).filter(Order.executor_id == executor_id)
    
    # Применяем фильтры
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    
    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)
    
    if status is not None:
        query = query.filter(Order.status == status)
    
    return query.count()

def get_all_orders_with_users_and_filters(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    executor_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение всех заказов с фильтрами и предзагруженными пользователями (оптимизированная версия)
    """
    from auth.models import User
    
    query = db.query(Order).options(
        joinedload(Order.customer),
        joinedload(Order.executor),
        joinedload(Order.products)
    )

    # Применяем фильтры
    if executor_id is not None:
        query = query.filter(Order.executor_id == executor_id)

    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)

    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)

    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)

    if status is not None:
        query = query.filter(Order.status == status)

    # Сортируем по дате создания (новые сначала)
    query = query.order_by(desc(Order.created_at))

    return query.offset(skip).limit(limit).all()

def get_all_orders(db: Session, skip: int = 0, limit: int = 100):
    """Получение всех заказов (для исполнителей)"""
    return db.query(Order).offset(skip).limit(limit).all()

def get_orders_by_status(db: Session, status: OrderStatus, skip: int = 0, limit: int = 100):
    """Получение заказов по статусу"""
    return db.query(Order).filter(Order.status == status).offset(skip).limit(limit).all()

def update_order_status(db: Session, order_id: int, status: OrderStatus):
    """Обновление статуса заказа"""
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    db_order.status = status
    if status == OrderStatus.COMPLETED:
        db_order.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order(db: Session, order_id: int, order_edit: OrderEdit):
    """
    Обновление заказа заказчиком
    
    Можно изменить:
    - Исполнителя (executor_id)
    - Список продуктов (products)
    
    При обновлении продуктов старые продукты удаляются и создаются новые.
    """
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    
    # Обновляем исполнителя, если указан
    if order_edit.executor_id is not None:
        db_order.executor_id = order_edit.executor_id
    
    # Обновляем продукты, если указаны
    if order_edit.products is not None:
        # Удаляем все старые продукты заказа
        db.query(Product).filter(Product.order_id == order_id).delete()
        
        # Создаем новые продукты
        for product_data in order_edit.products:
            db_product = Product(
                name=product_data.name,
                quantity=product_data.quantity,
                notes=product_data.notes,
                order_id=order_id
            )
            db.add(db_product)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def copy_order(db: Session, order_id: int, customer_id: int):
    """
    Копирование заказа заказчиком
    
    Создает новый заказ на основе существующего с:
    - Тем же исполнителем
    - Теми же продуктами (все продукты со статусом "не куплен")
    - Статусом PENDING (новый заказ)
    - Тем же заказчиком
    """
    # Получаем исходный заказ
    original_order = get_order(db, order_id)
    if not original_order:
        return None
    
    # Создаем новый заказ с теми же параметрами
    db_order = Order(
        customer_id=customer_id,
        executor_id=original_order.executor_id,
        status=OrderStatus.PENDING  # Копия всегда имеет статус "новый"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Копируем все продукты из исходного заказа
    for original_product in original_order.products:
        db_product = Product(
            name=original_product.name,
            quantity=original_product.quantity,
            notes=original_product.notes,
            order_id=db_order.id,
            is_purchased=False  # В копии все продукты не куплены
        )
        db.add(db_product)
    
    db.commit()
    db.refresh(db_order)
    return db_order

# CRUD операции для продуктов
def get_product(db: Session, product_id: int):
    """Получение продукта по ID"""
    return db.query(Product).filter(Product.id == product_id).first()

def update_product_purchase_status(db: Session, product_id: int, purchase_data: ProductPurchase, executor_id: int):
    """Обновление статуса покупки продукта"""
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    db_product.is_purchased = purchase_data.is_purchased
    if purchase_data.is_purchased:
        db_product.purchased_at = datetime.utcnow()
        db_product.purchased_by = executor_id
    else:
        db_product.purchased_at = None
        db_product.purchased_by = None
    
    db.commit()
    db.refresh(db_product)
    return db_product

def check_order_completion(db: Session, order_id: int):
    """Проверка, можно ли отметить заказ как исполненный"""
    order = get_order(db, order_id)
    if not order:
        return False
    
    # Проверяем, все ли продукты куплены
    total_products = len(order.products)
    purchased_products = sum(1 for product in order.products if product.is_purchased)
    
    return total_products > 0 and total_products == purchased_products

def get_order_summary(db: Session, order_id: int):
    """Получение сводки по заказу"""
    order = get_order(db, order_id)
    if not order:
        return None
    
    total_products = len(order.products)
    purchased_products = sum(1 for product in order.products if product.is_purchased)
    is_completable = check_order_completion(db, order_id)
    
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "executor_id": order.executor_id,
        "status": order.status,
        "created_at": order.created_at,
        "total_products": total_products,
        "purchased_products": purchased_products,
        "is_completable": is_completable
    }

# Административные CRUD операции для заказов
def get_all_orders_with_filters(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    executor_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение всех заказов с фильтрами (для администраторов)
    
    Args:
        db: Сессия базы данных
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        executor_id: Фильтр по ID исполнителя
        customer_id: Фильтр по ID заказчика
        date_from: Фильтр по дате создания (от)
        date_to: Фильтр по дате создания (до)
        status: Фильтр по статусу заказа
    
    Returns:
        Список заказов с примененными фильтрами
    """
    query = db.query(Order)
    
    # Применяем фильтры
    if executor_id is not None:
        query = query.filter(Order.executor_id == executor_id)
    
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    
    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)
    
    if status is not None:
        query = query.filter(Order.status == status)
    
    # Сортируем по дате создания (новые сначала)
    query = query.order_by(desc(Order.created_at))
    
    return query.offset(skip).limit(limit).all()

def get_orders_count_with_filters(
    db: Session,
    executor_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
):
    """
    Получение количества заказов с фильтрами (для пагинации)
    
    Args:
        db: Сессия базы данных
        executor_id: Фильтр по ID исполнителя
        customer_id: Фильтр по ID заказчика
        date_from: Фильтр по дате создания (от)
        date_to: Фильтр по дате создания (до)
        status: Фильтр по статусу заказа
    
    Returns:
        Количество заказов с примененными фильтрами
    """
    query = db.query(Order)
    
    # Применяем фильтры
    if executor_id is not None:
        query = query.filter(Order.executor_id == executor_id)
    
    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)
    
    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)
    
    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)
    
    if status is not None:
        query = query.filter(Order.status == status)
    
    return query.count()

# CRUD операции для сохраненных товаров
def create_saved_product(db: Session, saved_product: SavedProductCreate, user_id: int):
    """Создание сохраненного товара"""
    db_saved_product = SavedProduct(
        user_id=user_id,
        name=saved_product.name,
        quantity=saved_product.quantity,
        notes=saved_product.notes
    )
    db.add(db_saved_product)
    db.commit()
    db.refresh(db_saved_product)
    return db_saved_product

def get_saved_product(db: Session, saved_product_id: int, user_id: int):
    """Получение сохраненного товара по ID (только свой)"""
    return db.query(SavedProduct).filter(
        SavedProduct.id == saved_product_id,
        SavedProduct.user_id == user_id
    ).first()

def get_user_saved_products(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Получение всех сохраненных товаров пользователя"""
    return db.query(SavedProduct).filter(
        SavedProduct.user_id == user_id
    ).order_by(desc(SavedProduct.created_at)).offset(skip).limit(limit).all()

def get_user_saved_products_count(db: Session, user_id: int):
    """Получение количества сохраненных товаров пользователя"""
    return db.query(SavedProduct).filter(SavedProduct.user_id == user_id).count()

def update_saved_product(db: Session, saved_product_id: int, saved_product_update: SavedProductUpdate, user_id: int):
    """Обновление сохраненного товара"""
    db_saved_product = get_saved_product(db, saved_product_id, user_id)
    if not db_saved_product:
        return None
    
    if saved_product_update.name is not None:
        db_saved_product.name = saved_product_update.name
    if saved_product_update.quantity is not None:
        db_saved_product.quantity = saved_product_update.quantity
    if saved_product_update.notes is not None:
        db_saved_product.notes = saved_product_update.notes
    
    db.commit()
    db.refresh(db_saved_product)
    return db_saved_product

def delete_saved_product(db: Session, saved_product_id: int, user_id: int):
    """Удаление сохраненного товара"""
    db_saved_product = get_saved_product(db, saved_product_id, user_id)
    if not db_saved_product:
        return False
    
    db.delete(db_saved_product)
    db.commit()
    return True
