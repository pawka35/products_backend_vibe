"""
Тест для эндпоинта завершения заказа с комментарием
"""
import requests

BASE_URL = "http://localhost:8000"


def test_complete_order_with_comment():
    """
    Тест завершения заказа с комментарием исполнителя
    """
    print("\nТест завершения заказа с комментарием")
    print("=" * 60)
    
    # 1. Получаем токен администратора
    print("1. Получение токена администратора...")
    admin_login = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=admin_login)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения токена админа: {response.text}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   ✅ Токен администратора получен")
    
    # 2. Создаем тестовых пользователей
    print("\n2. Создание тестовых пользователей...")
    
    import random
    suffix = random.randint(1000, 9999)
    
    # Создаем заказчика
    customer_data = {
        "username": f"test_complete_customer_{suffix}",
        "email": f"complete_customer_{suffix}@test.com",
        "password": "TestPass123!",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=customer_data)
    if response.status_code != 200:
        print(f"   ❌ Ошибка создания заказчика: {response.text}")
        return
    
    customer = response.json()
    print(f"   ✅ Создан заказчик: {customer['username']}")
    
    # Создаем исполнителя
    executor_data = {
        "username": f"test_complete_executor_{suffix}",
        "email": f"complete_executor_{suffix}@test.com",
        "password": "TestPass123!",
        "role": "executor"
    }
    
    response = requests.post(f"{BASE_URL}/admin/users", json=executor_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"   ❌ Ошибка создания исполнителя: {response.text}")
        return
    
    executor = response.json()
    print(f"   ✅ Создан исполнитель: {executor['username']}")
    
    # 3. Получаем токены пользователей
    print("\n3. Получение токенов...")
    
    # Токен заказчика
    customer_login = {
        "username": customer_data['username'],
        "password": customer_data['password']
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=customer_login)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения токена заказчика: {response.text}")
        return
    
    customer_token = response.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    print("   ✅ Токен заказчика получен")
    
    # Токен исполнителя
    executor_login = {
        "username": executor_data['username'],
        "password": executor_data['password']
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=executor_login)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения токена исполнителя: {response.text}")
        return
    
    executor_token = response.json()["access_token"]
    executor_headers = {"Authorization": f"Bearer {executor_token}"}
    print("   ✅ Токен исполнителя получен")
    
    # 4. Создаем заказ
    print("\n4. Создание заказа...")
    order_data = {
        "executor_id": executor['id'],
        "products": [
            {
                "name": "Тестовый товар 1",
                "quantity": 2,
            },
            {
                "name": "Тестовый товар 2",
                "quantity": 1,
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/customer/orders", json=order_data, headers=customer_headers)
    if response.status_code != 200:
        print(f"   ❌ Ошибка создания заказа: {response.text}")
        return
    
    order = response.json()
    print(f"   ✅ Заказ создан с ID: {order['id']}, Статус: {order['status']}")
    
    # 5. Исполнитель берет заказ в работу
    print("\n5. Исполнитель берет заказ в работу...")
    status_update = {"status": "in_progress"}
    
    response = requests.put(
        f"{BASE_URL}/executor/orders/{order['id']}/status",
        json=status_update,
        headers=executor_headers
    )
    
    if response.status_code == 200:
        order = response.json()
        print(f"   ✅ Заказ взят в работу, статус: {order['status']}")
    else:
        print(f"   ❌ Ошибка: {response.text}")
        return
    
    # 6. Исполнитель отмечает все продукты как купленные
    print("\n6. Исполнитель отмечает продукты как купленные...")
    
    for product in order['products']:
        purchase_data = {
            "is_purchased": True,
            "notes": f"Куплено в магазине"
        }
        
        response = requests.put(
            f"{BASE_URL}/executor/products/{product['id']}/purchase",
            json=purchase_data,
            headers=executor_headers
        )
        
        if response.status_code == 200:
            print(f"   ✅ Товар '{product['name']}' отмечен как купленный")
        else:
            print(f"   ⚠️  Ошибка отметки товара: {response.text}")
    
    # 7. Тест 1: Завершение заказа БЕЗ комментария
    print("\n7. Тест 1: Завершение заказа без комментария...")
    
    # Создаем еще один заказ для этого теста
    response = requests.post(f"{BASE_URL}/customer/orders", json=order_data, headers=customer_headers)
    test_order_1 = response.json()
    
    # Берем в работу
    response = requests.put(
        f"{BASE_URL}/executor/orders/{test_order_1['id']}/status",
        json={"status": "in_progress"},
        headers=executor_headers
    )
    
    # Отмечаем все продукты как купленные
    for product in test_order_1['products']:
        requests.put(
            f"{BASE_URL}/executor/products/{product['id']}/purchase",
            json={"is_purchased": True},
            headers=executor_headers
        )
    
    # Завершаем без комментария
    response = requests.put(
        f"{BASE_URL}/executor/orders/{test_order_1['id']}/complete",
        headers=executor_headers
    )
    
    if response.status_code == 200:
        completed_order = response.json()
        print(f"   ✅ Заказ завершен без комментария")
        print(f"   Статус: {completed_order['status']}")
        print(f"   Комментарий: {completed_order.get('complete_comment', 'None')}")
        
        if completed_order['status'] != 'completed':
            print(f"   ⚠️  Статус должен быть 'completed', но получен '{completed_order['status']}'")
        
        if completed_order.get('complete_comment') is not None:
            print(f"   ⚠️  Комментарий должен быть None при завершении без комментария")
    else:
        print(f"   ❌ Ошибка завершения заказа: {response.text}")
    
    # 8. Тест 2: Завершение заказа С комментарием
    print("\n8. Тест 2: Завершение заказа с комментарием...")
    
    # Создаем третий заказ для этого теста
    response = requests.post(f"{BASE_URL}/customer/orders", json=order_data, headers=customer_headers)
    test_order_2 = response.json()
    
    # Берем в работу
    response = requests.put(
        f"{BASE_URL}/executor/orders/{test_order_2['id']}/status",
        json={"status": "in_progress"},
        headers=executor_headers
    )
    
    # Отмечаем все продукты как купленные
    for product in test_order_2['products']:
        requests.put(
            f"{BASE_URL}/executor/products/{product['id']}/purchase",
            json={"is_purchased": True},
            headers=executor_headers
        )
    
    # Завершаем С комментарием
    complete_data = {
        "complete_comment": "Все товары куплены и доставлены вовремя. Клиент доволен!"
    }
    
    response = requests.put(
        f"{BASE_URL}/executor/orders/{test_order_2['id']}/complete",
        json=complete_data,
        headers=executor_headers
    )
    
    if response.status_code == 200:
        completed_order = response.json()
        print(f"   ✅ Заказ завершен с комментарием")
        print(f"   Статус: {completed_order['status']}")
        print(f"   Комментарий: '{completed_order.get('complete_comment', 'None')}'")
        
        if completed_order['status'] != 'completed':
            print(f"   ⚠️  Статус должен быть 'completed', но получен '{completed_order['status']}'")
        
        if completed_order.get('complete_comment') != complete_data['complete_comment']:
            print(f"   ⚠️  Комментарий не совпадает!")
            print(f"      Ожидалось: {complete_data['complete_comment']}")
            print(f"      Получено: {completed_order.get('complete_comment')}")
    else:
        print(f"   ❌ Ошибка завершения заказа: {response.text}")
    
    # 9. Проверяем, что комментарий виден при получении заказа
    print("\n9. Проверка видимости комментария при получении заказа...")
    
    response = requests.get(
        f"{BASE_URL}/customer/orders/{test_order_2['id']}",
        headers=customer_headers
    )
    
    if response.status_code == 200:
        order_details = response.json()
        print(f"   ✅ Заказ получен")
        print(f"   Комментарий из заказа: '{order_details.get('complete_comment', 'None')}'")
        
        if order_details.get('complete_comment') == complete_data['complete_comment']:
            print(f"   ✅ Комментарий корректно сохранен и отображается")
        else:
            print(f"   ⚠️  Комментарий не совпадает при получении заказа!")
    else:
        print(f"   ❌ Ошибка получения заказа: {response.text}")
    
    # 10. Очистка - удаляем тестовых пользователей
    print("\n10. Очистка тестовых данных...")
    
    for user_id, username in [(customer['id'], customer['username']), (executor['id'], executor['username'])]:
        response = requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=admin_headers)
        if response.status_code in [200, 204]:
            print(f"   ✅ Пользователь {username} удален")
    
    print("\n" + "=" * 60)
    print("✅ Тест завершен успешно!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_complete_order_with_comment()
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

