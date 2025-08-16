import requests
import json

BASE_URL = "http://localhost:8000"

def test_orders_functionality():
    """Тест функционала заказов"""
    
    print("Тест функционала заказов FastAPI")
    print("=" * 50)
    
    # 1. Создаем заказчика
    print("1. Создание заказчика...")
    customer_data = {
        "username": "customer1",
        "email": "customer1@example.com",
        "password": "customer123",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=customer_data)
    if response.status_code != 200:
        print(f"   Ошибка создания заказчика: {response.text}")
        return
    
    customer = response.json()
    print(f"   Заказчик создан: {customer['username']}")
    
    # 2. Создаем исполнителя
    print("\n2. Создание исполнителя...")
    executor_data = {
        "username": "executor1",
        "email": "executor1@example.com",
        "password": "executor123",
        "role": "executor"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=executor_data)
    if response.status_code != 200:
        print(f"   Ошибка создания исполнителя: {response.text}")
        return
    
    executor = response.json()
    print(f"   Исполнитель создан: {executor['username']}")
    
    # 3. Получаем токен для заказчика
    print("\n3. Получение токена для заказчика...")
    customer_login = {
        "username": "customer1",
        "password": "customer123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=customer_login)
    if response.status_code != 200:
        print(f"   Ошибка получения токена заказчика: {response.text}")
        return
    
    customer_token = response.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    print("   Токен заказчика получен")
    
    # 4. Создаем заказ
    print("\n4. Создание заказа...")
    order_data = {
        "products": [
            {
                "name": "Хлеб",
                "quantity": 2,
                "notes": "Свежий белый хлеб"
            },
            {
                "name": "Молоко",
                "quantity": 1,
                "notes": "3.2% жирности"
            },
            {
                "name": "Яблоки",
                "quantity": 5,
                "notes": "Красные, сладкие"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/orders/", json=order_data, headers=customer_headers)
    if response.status_code != 200:
        print(f"   Ошибка создания заказа: {response.text}")
        return
    
    order = response.json()
    order_id = order["id"]
    print(f"   Заказ создан с ID: {order_id}")
    print(f"   Количество продуктов: {len(order['products'])}")
    
    # 5. Получаем токен для исполнителя
    print("\n5. Получение токена для исполнителя...")
    executor_login = {
        "username": "executor1",
        "password": "executor123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=executor_login)
    if response.status_code != 200:
        print(f"   Ошибка получения токена исполнителя: {response.text}")
        return
    
    executor_token = response.json()["access_token"]
    executor_headers = {"Authorization": f"Bearer {executor_token}"}
    print("   Токен исполнителя получен")
    
    # 6. Исполнитель просматривает доступные заказы
    print("\n6. Просмотр доступных заказов исполнителем...")
    response = requests.get(f"{BASE_URL}/executor/orders", headers=executor_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения заказов: {response.text}")
        return
    
    available_orders = response.json()
    print(f"   Найдено доступных заказов: {len(available_orders)}")
    
    # 7. Исполнитель начинает исполнение заказа
    print("\n7. Начало исполнения заказа...")
    response = requests.put(f"{BASE_URL}/executor/orders/{order_id}/start", headers=executor_headers)
    if response.status_code != 200:
        print(f"   Ошибка начала исполнения: {response.text}")
        return
    
    print("   Заказ переведен в статус 'в процессе'")
    
    # 8. Исполнитель отмечает продукты как купленные
    print("\n8. Отметка продуктов как купленных...")
    
    # Получаем детали заказа для получения ID продуктов
    response = requests.get(f"{BASE_URL}/executor/orders/{order_id}", headers=executor_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения деталей заказа: {response.text}")
        return
    
    order_details = response.json()
    
    for i, product in enumerate(order_details["products"]):
        print(f"   Отмечаем продукт '{product['name']}' как купленный...")
        purchase_data = {
            "is_purchased": True,
            "notes": f"Куплено исполнителем {executor['username']}"
        }
        
        response = requests.put(
            f"{BASE_URL}/executor/products/{product['id']}/purchase", 
            json=purchase_data, 
            headers=executor_headers
        )
        
        if response.status_code != 200:
            print(f"     Ошибка: {response.text}")
        else:
            print(f"     Продукт '{product['name']}' отмечен как купленный")
    
    # 9. Проверяем статус заказа
    print("\n9. Проверка статуса заказа...")
    response = requests.get(f"{BASE_URL}/orders/{order_id}/summary", headers=customer_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения сводки: {response.text}")
        return
    
    summary = response.json()
    print(f"   Статус заказа: {summary['status']}")
    print(f"   Всего продуктов: {summary['total_products']}")
    print(f"   Куплено продуктов: {summary['purchased_products']}")
    print(f"   Можно завершить: {summary['is_completable']}")
    
    # 10. Завершаем заказ
    print("\n10. Завершение заказа...")
    response = requests.put(f"{BASE_URL}/executor/orders/{order_id}/complete", headers=executor_headers)
    if response.status_code != 200:
        print(f"   Ошибка завершения заказа: {response.text}")
        return
    
    print("   Заказ успешно завершен!")
    
    # 11. Финальная проверка
    print("\n11. Финальная проверка...")
    response = requests.get(f"{BASE_URL}/orders/{order_id}", headers=customer_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения заказа: {response.text}")
        return
    
    final_order = response.json()
    print(f"   Финальный статус: {final_order['status']}")
    print(f"   Время завершения: {final_order['completed_at']}")
    
    print("\n" + "=" * 50)
    print("Тест завершен успешно! 🎉")

if __name__ == "__main__":
    test_orders_functionality()
