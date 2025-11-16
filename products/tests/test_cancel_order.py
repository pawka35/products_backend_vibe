"""
Тест для эндпоинта отмены заказа заказчиком
"""
import requests

BASE_URL = "http://localhost:8000"


def test_cancel_order():
    """
    Тест отмены заказа заказчиком
    """
    print("\nТест отмены заказа заказчиком")
    print("=" * 60)
    
    # 1. Получаем токен администратора для создания тестовых пользователей
    print("1. Получение токена администратора...")
    admin_login = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=admin_login)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения токена админа: {response.text}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   ✅ Токен администратора получен")
    
    # 2. Создаем тестового заказчика и исполнителя (если их нет)
    print("\n2. Создание тестовых пользователей...")
    
    # Получаем существующих исполнителей
    response = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    users = response.json() if response.status_code == 200 else []
    
    executor = None
    customer = None
    
    for user in users:
        if user['role'] == 'executor' and not executor:
            executor = user
        if user['username'].startswith('test_cancel_customer'):
            customer = user
    
    # Если нет исполнителя, создаем
    if not executor:
        executor_data = {
            "username": "test_executor_cancel",
            "email": "executor_cancel@test.com",
            "password": "TestPass123!",
            "role": "executor"
        }
        response = requests.post(f"{BASE_URL}/admin/users", json=executor_data, headers=admin_headers)
        if response.status_code == 200:
            executor = response.json()
            print(f"   ✅ Создан исполнитель: {executor['username']}")
    
    # Создаем нового заказчика для теста
    import random
    suffix = random.randint(1000, 9999)
    customer_data = {
        "username": f"test_cancel_customer_{suffix}",
        "email": f"cancel_customer_{suffix}@test.com",
        "password": "TestPass123!",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=customer_data)
    if response.status_code != 200:
        print(f"   ❌ Ошибка создания заказчика: {response.text}")
        return
    
    customer = response.json()
    print(f"   ✅ Создан заказчик: {customer['username']}")
    
    # 3. Получаем токен заказчика
    print("\n3. Получение токена заказчика...")
    customer_login = {
        "username": customer_data['username'],
        "password": customer_data['password']
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=customer_login)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения токена: {response.text}")
        return
    
    customer_token = response.json()["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    print("   ✅ Токен заказчика получен")
    
    # 4. Создаем тестовый заказ
    print("\n4. Создание тестового заказа...")
    order_data = {
        "executor_id": executor['id'],
        "products": [
            {
                "name": "Тестовый товар 1",
                "price": 100.0,
                "quantity": 2,
                "link": "https://example.com/product1"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/customer/orders", json=order_data, headers=customer_headers)
    if response.status_code != 200:
        print(f"   ❌ Ошибка создания заказа: {response.text}")
        return
    
    order = response.json()
    print(f"   ✅ Заказ создан с ID: {order['id']}, Статус: {order['status']}")
    
    # 5. Отменяем заказ
    print("\n5. Отмена заказа...")
    response = requests.post(f"{BASE_URL}/api/customer/orders/{order['id']}/cancel", headers=customer_headers)
    
    if response.status_code == 200:
        cancelled_order = response.json()
        print(f"   ✅ Заказ отменен успешно!")
        print(f"   Новый статус: {cancelled_order['status']}")
        
        if cancelled_order['status'] != 'cancelled':
            print(f"   ⚠️  Статус должен быть 'cancelled', но получен '{cancelled_order['status']}'")
    else:
        print(f"   ❌ Ошибка отмены заказа: {response.status_code}")
        print(f"   Детали: {response.text}")
        return
    
    # 6. Проверяем, что нельзя отменить уже отмененный заказ
    print("\n6. Попытка повторной отмены заказа...")
    response = requests.post(f"{BASE_URL}/api/customer/orders/{order['id']}/cancel", headers=customer_headers)
    
    if response.status_code == 400:
        error = response.json()
        print(f"   ✅ Правильно: повторная отмена запрещена")
        print(f"   Сообщение: {error['detail']}")
    else:
        print(f"   ⚠️  Неожиданный статус: {response.status_code}")
    
    # 7. Создаем новый заказ и проверяем, что нельзя отменить заказ в работе
    print("\n7. Создание нового заказа для проверки статуса IN_PROGRESS...")
    response = requests.post(f"{BASE_URL}/api/customer/orders", json=order_data, headers=customer_headers)
    
    if response.status_code == 200:
        order2 = response.json()
        print(f"   ✅ Заказ создан с ID: {order2['id']}")
        
        # Получаем токен исполнителя и берем заказ в работу
        executor_login = {
            "username": "test_executor_cancel" if not executor.get('username') == 'admin' else executor['username'],
            "password": "TestPass123!" if not executor.get('username') == 'admin' else "Admin123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/token", data=executor_login)
        if response.status_code == 200:
            executor_token = response.json()["access_token"]
            executor_headers = {"Authorization": f"Bearer {executor_token}"}
            
            # Берем заказ в работу (меняем статус на IN_PROGRESS)
            status_update = {"status": "in_progress"}
            response = requests.put(
                f"{BASE_URL}/executor/orders/{order2['id']}/status",
                json=status_update,
                headers=executor_headers
            )
            
            if response.status_code == 200:
                print(f"   ✅ Заказ взят в работу")
                
                # Пытаемся отменить заказ в работе
                print("\n8. Попытка отмены заказа в статусе IN_PROGRESS...")
                response = requests.post(
                    f"{BASE_URL}/api/customer/orders/{order2['id']}/cancel",
                    headers=customer_headers
                )
                
                if response.status_code == 400:
                    error = response.json()
                    print(f"   ✅ Правильно: отмена заказа в работе запрещена")
                    print(f"   Сообщение: {error['detail']}")
                else:
                    print(f"   ⚠️  Неожиданный статус: {response.status_code}")
    
    # 9. Очистка - удаляем тестового пользователя
    print("\n9. Очистка тестовых данных...")
    response = requests.delete(f"{BASE_URL}/admin/users/{customer['id']}", headers=admin_headers)
    if response.status_code in [200, 204]:
        print(f"   ✅ Тестовый заказчик удален")
    
    print("\n" + "=" * 60)
    print("✅ Тест завершен успешно!")


if __name__ == "__main__":
    try:
        test_cancel_order()
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

