#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов в системе
"""

import sys
import time

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск всех тестов FastAPI системы")
    print("=" * 60)
    
    # Тест аутентификации
    print("\n🔐 Тест аутентификации...")
    try:
        from auth import test_auth_flow
        test_auth_flow()
        print("✅ Тест аутентификации пройден")
    except Exception as e:
        print(f"❌ Тест аутентификации провален: {e}")
    
    # Тест API
    print("\n🌐 Тест API...")
    try:
        from app import test_api_flow
        test_api_flow()
        print("✅ Тест API пройден")
    except Exception as e:
        print(f"❌ Тест API провален: {e}")
    
    # Тест административных функций
    print("\n🔴 Тест административных функций...")
    try:
        from app import test_admin_functions
        test_admin_functions()
        print("✅ Тест административных функций пройден")
    except Exception as e:
        print(f"❌ Тест административных функций провален: {e}")
    
    # Тест функционала заказов
    print("\n📦 Тест функционала заказов...")
    try:
        from products import test_orders_functionality
        test_orders_functionality()
        print("✅ Тест функционала заказов пройден")
    except Exception as e:
        print(f"❌ Тест функционала заказов провален: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Все тесты завершены!")

def run_specific_test(test_name):
    """Запуск конкретного теста"""
    print(f"🎯 Запуск теста: {test_name}")
    
    if test_name == "auth":
        from auth import test_auth_flow
        test_auth_flow()
    elif test_name == "api":
        from app import test_api_flow
        test_api_flow()
    elif test_name == "admin":
        from app import test_admin_functions
        test_admin_functions()
    elif test_name == "orders":
        from products import test_orders_functionality
        test_orders_functionality()
    else:
        print(f"❌ Неизвестный тест: {test_name}")
        print("Доступные тесты: auth, api, admin, orders")
        return
    
    print(f"✅ Тест {test_name} завершен успешно!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        run_all_tests()
