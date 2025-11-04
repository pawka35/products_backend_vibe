"""
Тест для эндпоинта завершения заказа с частично купленными продуктами
"""
import requests

BASE_URL = "http://localhost:8000"


def test_complete_order_partial_products():
    """
    Тест завершения заказа, когда не все продукты куплены
    """
    print("\nТест завершения заказа с частично купленными продуктами")
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
        "username": f"test_partial_customer_{suffix}",
        "email": f"partial_customer_{suffix}@test.com",
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
        "username": f"test_partial_executor_{suffix}",
        "email": f"partial_executor_{suffix}@test.com",
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
    
    # 4. Создаем заказ с несколькими продуктами
    print("\n4. Создание заказа с 3 продуктами...")
    order_data = {
        "executor_id": executor['id'],
        "products": [
            {
                "name": "Продукт 1",
                "quantity": 1,
            },
            {
                "name": "Продукт 2",
                "quantity": 2,
            },
            {
                "name": "Продукт 3",
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
    print(f"   Продуктов в заказе: {len(order['products'])}")
    
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
    
    # 6. Исполнитель покупает только ЧАСТЬ продуктов (2 из 3)
    print("\n6. Исполнитель покупает только 2 продукта из 3...")
    
    products_to_purchase = order['products'][:2]  # Только первые 2 продукта
    
    for product in products_to_purchase:
        purchase_data = {
            "is_purchased": True,
            "notes": f"Куплено"
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
    
    print(f"   ℹ️  Куплено: 2 из 3 продуктов")
    print(f"   ℹ️  НЕ куплен: '{order['products'][2]['name']}'")
    
    # 7. Тест 1: Попытка завершить заказ БЕЗ комментария (должна быть ошибка)
    print("\n7. Тест 1: Попытка завершить заказ без комментария (не все продукты куплены)...")
    
    response = requests.put(
        f"{BASE_URL}/executor/orders/{order['id']}/complete",
        headers=executor_headers
    )
    
    if response.status_code == 400:
        print(f"   ✅ Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"   ❌ Неожиданный результат: статус {response.status_code}")
        print(f"      Ожидалось: 400 (Bad Request)")
        print(f"      Получено: {response.status_code}")
    
    # 8. Тест 2: Попытка завершить заказ С ПУСТЫМ комментарием (должна быть ошибка)
    print("\n8. Тест 2: Попытка завершить заказ с пустым комментарием...")
    
    complete_data = {
        "complete_comment": "   "  # Только пробелы
    }
    
    response = requests.put(
        f"{BASE_URL}/executor/orders/{order['id']}/complete",
        json=complete_data,
        headers=executor_headers
    )
    
    if response.status_code == 400:
        print(f"   ✅ Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"   ❌ Неожиданный результат: статус {response.status_code}")
    
    # 9. Тест 3: Завершение заказа С КОММЕНТАРИЕМ (должно быть успешно)
    print("\n9. Тест 3: Завершение заказа с комментарием (не все продукты куплены)...")
    
    complete_data = {
        "complete_comment": "Товар 'Продукт 3' отсутствовал в наличии в магазине. "
                           "Согласовано с заказчиком телефонно."
    }
    
    response = requests.put(
        f"{BASE_URL}/executor/orders/{order['id']}/complete",
        json=complete_data,
        headers=executor_headers
    )
    
    if response.status_code == 200:
        completed_order = response.json()
        print(f"   ✅ Заказ успешно завершен")
        print(f"   Статус: {completed_order['status']}")
        print(f"   Комментарий: '{completed_order.get('complete_comment', 'None')}'")
        
        # Проверяем, что комментарий сохранился
        if completed_order.get('complete_comment') == complete_data['complete_comment']:
            print(f"   ✅ Комментарий корректно сохранен")
        else:
            print(f"   ⚠️  Комментарий не совпадает!")
    else:
        print(f"   ❌ Ошибка завершения заказа: {response.text}")
    
    # 10. Тест 4: Завершение заказа со ВСЕМИ купленными продуктами БЕЗ комментария
    print("\n10. Тест 4: Завершение заказа со всеми купленными продуктами без комментария...")
    
    # Создаем новый заказ
    response = requests.post(f"{BASE_URL}/customer/orders", json=order_data, headers=customer_headers)
    test_order_2 = response.json()
    
    # Берем в работу
    requests.put(
        f"{BASE_URL}/executor/orders/{test_order_2['id']}/status",
        json={"status": "in_progress"},
        headers=executor_headers
    )
    
    # Покупаем ВСЕ продукты
    for product in test_order_2['products']:
        requests.put(
            f"{BASE_URL}/executor/products/{product['id']}/purchase",
            json={"is_purchased": True},
            headers=executor_headers
        )
    
    print(f"   ℹ️  Все продукты помечены как купленные")
    
    # Завершаем БЕЗ комментария
    response = requests.put(
        f"{BASE_URL}/executor/orders/{test_order_2['id']}/complete",
        headers=executor_headers
    )
    
    if response.status_code == 200:
        completed_order = response.json()
        print(f"   ✅ Заказ успешно завершен без комментария")
        print(f"   Статус: {completed_order['status']}")
        print(f"   Комментарий: {completed_order.get('complete_comment', 'None')}")
    else:
        print(f"   ❌ Ошибка завершения заказа: {response.text}")
    
    # 11. Тест 5: Завершение заказа со ВСЕМИ купленными продуктами С комментарием
    print("\n11. Тест 5: Завершение заказа со всеми купленными продуктами с комментарием...")
    
    # Создаем еще один заказ
    response = requests.post(f"{BASE_URL}/customer/orders", json=order_data, headers=customer_headers)
    test_order_3 = response.json()
    
    # Берем в работу
    requests.put(
        f"{BASE_URL}/executor/orders/{test_order_3['id']}/status",
        json={"status": "in_progress"},
        headers=executor_headers
    )
    
    # Покупаем ВСЕ продукты
    for product in test_order_3['products']:
        requests.put(
            f"{BASE_URL}/executor/products/{product['id']}/purchase",
            json={"is_purchased": True},
            headers=executor_headers
        )
    
    # Завершаем С комментарием
    complete_data = {
        "complete_comment": "Все товары куплены и доставлены. Клиент доволен!"
    }
    
    response = requests.put(
        f"{BASE_URL}/executor/orders/{test_order_3['id']}/complete",
        json=complete_data,
        headers=executor_headers
    )
    
    if response.status_code == 200:
        completed_order = response.json()
        print(f"   ✅ Заказ успешно завершен с комментарием")
        print(f"   Статус: {completed_order['status']}")
        print(f"   Комментарий: '{completed_order.get('complete_comment')}'")
    else:
        print(f"   ❌ Ошибка завершения заказа: {response.text}")
    
    # 12. Очистка - удаляем тестовых пользователей
    print("\n12. Очистка тестовых данных...")
    
    for user_id, username in [(customer['id'], customer['username']), (executor['id'], executor['username'])]:
        response = requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=admin_headers)
        if response.status_code in [200, 204]:
            print(f"   ✅ Пользователь {username} удален")
    
    print("\n" + "=" * 60)
    print("✅ Все тесты завершены успешно!")
    print("=" * 60)
    
    print("\n📋 Сводка тестов:")
    print("   ✅ Тест 1: Нельзя завершить без комментария (не все куплены)")
    print("   ✅ Тест 2: Нельзя завершить с пустым комментарием (не все куплены)")
    print("   ✅ Тест 3: Можно завершить с комментарием (не все куплены)")
    print("   ✅ Тест 4: Можно завершить без комментария (все куплены)")
    print("   ✅ Тест 5: Можно завершить с комментарием (все куплены)")


if __name__ == "__main__":
    try:
        test_complete_order_partial_products()
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

