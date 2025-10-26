#!/usr/bin/env python3
"""
Тест API для проверки обязательного указания исполнителя при создании заказа
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Проверка подключения к API"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API доступен")
            return True
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False

def register_test_user(username, email, password, role="customer"):
    """Регистрация тестового пользователя"""
    data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    
    if response.status_code == 200:
        print(f"✅ Пользователь {username} зарегистрирован")
        return response.json()
    else:
        print(f"❌ Ошибка регистрации {username}: {response.status_code} - {response.text}")
        return None

def login_user(username, password):
    """Вход пользователя"""
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✅ Пользователь {username} вошел в систему")
        return token_data["access_token"]
    else:
        print(f"❌ Ошибка входа {username}: {response.status_code} - {response.text}")
        return None

def get_headers(token):
    """Получение заголовков с токеном"""
    return {"Authorization": f"Bearer {token}"}

def test_create_order_with_executor():
    """Тест создания заказа с исполнителем"""
    print("\n🧪 Тест создания заказа с исполнителем...")
    
    # Регистрируем заказчика
    customer = register_test_user("test_customer_api", "customer@example.com", "password123", "customer")
    if not customer:
        return False
    
    # Регистрируем исполнителя
    executor = register_test_user("test_executor_api", "executor@example.com", "password123", "executor")
    if not executor:
        return False
    
    # Входим как заказчик
    customer_token = login_user("test_customer_api", "password123")
    if not customer_token:
        return False
    
    # Создаем заказ с исполнителем
    order_data = {
        "products": [
            {
                "name": "Тестовый продукт API",
                "quantity": 2,
                "notes": "Тестовые заметки для API"
            }
        ],
        "executor_id": executor["id"]
    }
    
    response = requests.post(
        f"{BASE_URL}/orders/",
        json=order_data,
        headers=get_headers(customer_token)
    )
    
    if response.status_code == 200:
        order = response.json()
        print(f"✅ Заказ создан с ID: {order['id']}")
        print(f"   Заказчик: {order['customer_id']}")
        print(f"   Исполнитель: {order['executor_id']}")
        print(f"   Статус: {order['status']}")
        return True
    else:
        print(f"❌ Ошибка создания заказа: {response.status_code} - {response.text}")
        return False

def test_create_order_without_executor():
    """Тест создания заказа без исполнителя (должен упасть)"""
    print("\n🧪 Тест создания заказа без исполнителя (ожидаем ошибку)...")
    
    # Входим как заказчик
    customer_token = login_user("test_customer_api", "password123")
    if not customer_token:
        return False
    
    # Создаем заказ без executor_id
    order_data = {
        "products": [
            {
                "name": "Тестовый продукт без исполнителя",
                "quantity": 1
            }
        ]
        # executor_id отсутствует
    }
    
    response = requests.post(
        f"{BASE_URL}/orders/",
        json=order_data,
        headers=get_headers(customer_token)
    )
    
    if response.status_code == 422:  # Validation Error
        print("✅ Ожидаемая ошибка валидации получена")
        print(f"   Детали: {response.json()}")
        return True
    else:
        print(f"❌ Неожиданный ответ: {response.status_code} - {response.text}")
        return False

def test_create_order_with_invalid_executor():
    """Тест создания заказа с недействительным исполнителем"""
    print("\n🧪 Тест создания заказа с недействительным исполнителем...")
    
    # Входим как заказчик
    customer_token = login_user("test_customer_api", "password123")
    if not customer_token:
        return False
    
    # Создаем заказ с несуществующим executor_id
    order_data = {
        "products": [
            {
                "name": "Тестовый продукт с недействительным исполнителем",
                "quantity": 1
            }
        ],
        "executor_id": 99999  # Несуществующий ID
    }
    
    response = requests.post(
        f"{BASE_URL}/orders/",
        json=order_data,
        headers=get_headers(customer_token)
    )
    
    if response.status_code == 404:
        print("✅ Ожидаемая ошибка 'Исполнитель не найден' получена")
        return True
    else:
        print(f"❌ Неожиданный ответ: {response.status_code} - {response.text}")
        return False

def test_get_available_executors():
    """Тест получения списка доступных исполнителей"""
    print("\n🧪 Тест получения списка доступных исполнителей...")
    
    # Входим как заказчик
    customer_token = login_user("test_customer_api", "password123")
    if not customer_token:
        return False
    
    response = requests.get(
        f"{BASE_URL}/orders/executors",
        headers=get_headers(customer_token)
    )
    
    if response.status_code == 200:
        executors = response.json()
        print(f"✅ Получен список исполнителей: {len(executors)} пользователей")
        for executor in executors:
            print(f"   - {executor['username']} (ID: {executor['id']}, роль: {executor['role']})")
        return True
    else:
        print(f"❌ Ошибка получения исполнителей: {response.status_code} - {response.text}")
        return False

def test_create_order_with_customer_as_executor():
    """Тест создания заказа, где заказчик назначает себя исполнителем"""
    print("\n🧪 Тест создания заказа с заказчиком как исполнителем...")
    
    # Входим как заказчик
    customer_token = login_user("test_customer_api", "password123")
    if not customer_token:
        return False
    
    # Получаем информацию о текущем пользователе
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=get_headers(customer_token)
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения информации о пользователе: {response.status_code}")
        return False
    
    customer_info = response.json()
    
    # Создаем заказ, где заказчик назначает себя исполнителем
    order_data = {
        "products": [
            {
                "name": "Тестовый продукт с самоназначением",
                "quantity": 1
            }
        ],
        "executor_id": customer_info["id"]  # Заказчик назначает себя
    }
    
    response = requests.post(
        f"{BASE_URL}/orders/",
        json=order_data,
        headers=get_headers(customer_token)
    )
    
    if response.status_code == 400:
        print("✅ Ожидаемая ошибка 'Нельзя назначить заказ самому себе' получена")
        return True
    else:
        print(f"❌ Неожиданный ответ: {response.status_code} - {response.text}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов API для обязательного указания исполнителя")
    print("=" * 70)
    
    # Проверяем подключение к API
    if not test_api_connection():
        print("❌ Не удается подключиться к API. Убедитесь, что сервер запущен.")
        return 1
    
    # Запускаем тесты
    tests = [
        ("Создание заказа с исполнителем", test_create_order_with_executor),
        ("Создание заказа без исполнителя", test_create_order_without_executor),
        ("Создание заказа с недействительным исполнителем", test_create_order_with_invalid_executor),
        ("Получение списка исполнителей", test_get_available_executors),
        ("Создание заказа с самоназначением", test_create_order_with_customer_as_executor),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим результаты
    print("\n" + "=" * 70)
    print("📊 Результаты тестов API:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Пройдено тестов: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 Все тесты API пройдены успешно!")
        return 0
    else:
        print(f"\n💥 {len(results) - passed} тестов провалены!")
        return 1

if __name__ == "__main__":
    exit(main())
