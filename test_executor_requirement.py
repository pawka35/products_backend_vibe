#!/usr/bin/env python3
"""
Тест для проверки обязательного указания исполнителя при создании заказа
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import get_db
from products.schemas import OrderCreate, ProductCreate
from products.crud import create_order
from auth.models import User, UserRole
from auth.utils.auth_utils import get_password_hash

def test_order_with_executor():
    """Тест создания заказа с исполнителем"""
    print("🧪 Тестируем создание заказа с исполнителем...")
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # Создаем тестового заказчика
        customer = User(
            username="test_customer",
            email="customer@test.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.CUSTOMER,
            is_active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"✅ Создан заказчик с ID: {customer.id}")
        
        # Создаем тестового исполнителя
        executor = User(
            username="test_executor",
            email="executor@test.com",
            hashed_password=get_password_hash("password123"),
            role=UserRole.EXECUTOR,
            is_active=True
        )
        db.add(executor)
        db.commit()
        db.refresh(executor)
        print(f"✅ Создан исполнитель с ID: {executor.id}")
        
        # Создаем заказ с исполнителем
        order_data = OrderCreate(
            products=[
                ProductCreate(
                    name="Тестовый продукт",
                    quantity=2,
                    notes="Тестовые заметки"
                )
            ],
            executor_id=executor.id
        )
        
        order = create_order(db, order_data, customer.id)
        print(f"✅ Заказ создан с ID: {order.id}")
        print(f"   Заказчик: {order.customer_id}")
        print(f"   Исполнитель: {order.executor_id}")
        print(f"   Статус: {order.status}")
        print(f"   Продуктов: {len(order.products)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    finally:
        db.close()

def test_order_without_executor():
    """Тест создания заказа без исполнителя (должен упасть)"""
    print("\n🧪 Тестируем создание заказа без исполнителя (ожидаем ошибку)...")
    
    db = next(get_db())
    
    try:
        # Создаем заказ без executor_id (это должно вызвать ошибку)
        order_data = OrderCreate(
            products=[
                ProductCreate(
                    name="Тестовый продукт",
                    quantity=1
                )
            ]
            # executor_id отсутствует
        )
        
        # Это должно вызвать ошибку валидации Pydantic
        print("❌ Ошибка: заказ был создан без executor_id")
        return False
        
    except Exception as e:
        print(f"✅ Ожидаемая ошибка: {e}")
        return True
    finally:
        db.close()

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов для обязательного указания исполнителя")
    print("=" * 60)
    
    test1_passed = test_order_with_executor()
    test2_passed = test_order_without_executor()
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестов:")
    print(f"   Тест 1 (с исполнителем): {'✅ ПРОЙДЕН' if test1_passed else '❌ ПРОВАЛЕН'}")
    print(f"   Тест 2 (без исполнителя): {'✅ ПРОЙДЕН' if test2_passed else '❌ ПРОВАЛЕН'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("\n💥 Некоторые тесты провалены!")
        return 1

if __name__ == "__main__":
    exit(main())
