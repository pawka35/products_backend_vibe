from sqlalchemy.orm import Session
from products.models import Product, Order, OrderStatus
from products.schemas import ProductCreate, OrderCreate, ProductPurchase
from datetime import datetime

# CRUD операции для заказов
def create_order(db: Session, order: OrderCreate, customer_id: int):
    """Создание нового заказа"""
    db_order = Order(customer_id=customer_id)
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
    """Получение заказов пользователя"""
    return db.query(Order).filter(Order.customer_id == user_id).offset(skip).limit(limit).all()

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
        "status": order.status,
        "created_at": order.created_at,
        "total_products": total_products,
        "purchased_products": purchased_products,
        "is_completable": is_completable
    }
