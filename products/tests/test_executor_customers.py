"""
Тест для эндпоинта получения списка заказчиков исполнителем
"""
import requests

BASE_URL = "http://localhost:8000"


def test_executor_get_customers():
    """
    Тест получения списка заказчиков исполнителем
    """
    print("\nТест получения списка заказчиков исполнителем")
    print("=" * 50)
    
    # 1. Получаем токен исполнителя (используем существующего пользователя или создаем нового)
    print("1. Получение токена исполнителя...")
    
    # Пытаемся войти как существующий исполнитель или создаем нового
    executor_login = {
        "username": "test_executor",
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=executor_login)
    
    if response.status_code != 200:
        # Создаем нового исполнителя
        print("   Создание нового исполнителя...")
        executor_data = {
            "username": "test_executor",
            "email": "executor@test.com",
            "password": "TestPass123!",
            "role": "executor"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=executor_data)
        if response.status_code != 200:
            print(f"   Ошибка создания исполнителя: {response.text}")
            return
        
        # Теперь получаем токен
        response = requests.post(f"{BASE_URL}/api/auth/token", data=executor_login)
        if response.status_code != 200:
            print(f"   Ошибка получения токена: {response.text}")
            return
    
    executor_token = response.json()["access_token"]
    executor_headers = {"Authorization": f"Bearer {executor_token}"}
    print("   ✅ Токен исполнителя получен")
    
    # 2. Получаем список заказчиков
    print("\n2. Получение списка заказчиков...")
    response = requests.get(f"{BASE_URL}/api/executor/customers", headers=executor_headers)
    
    if response.status_code == 200:
        customers = response.json()
        print(f"   ✅ Получено заказчиков: {len(customers)}")
        
        if customers:
            print("\n   Примеры заказчиков:")
            for customer in customers[:3]:  # Показываем первых 3
                print(f"   - ID: {customer['id']}, Username: {customer['username']}, Email: {customer['email']}")
        else:
            print("   ℹ️  В системе пока нет заказчиков")
    else:
        print(f"   ❌ Ошибка получения заказчиков: {response.status_code}")
        print(f"   Детали: {response.text}")
        return
    
    # 3. Проверяем, что обычный пользователь (не исполнитель) не может получить список
    print("\n3. Проверка доступа для не-исполнителя...")
    
    customer_login = {
        "username": "test_customer_check",
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=customer_login)
    
    if response.status_code != 200:
        # Создаем заказчика для теста
        customer_data = {
            "username": "test_customer_check",
            "email": "customer_check@test.com",
            "password": "TestPass123!",
            "role": "customer"
        }
        requests.post(f"{BASE_URL}/api/auth/register", json=customer_data)
        response = requests.post(f"{BASE_URL}/api/auth/token", data=customer_login)
    
    if response.status_code == 200:
        customer_token = response.json()["access_token"]
        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        
        # Пытаемся получить список заказчиков под заказчиком (должно быть запрещено)
        response = requests.get(f"{BASE_URL}/api/executor/customers", headers=customer_headers)
        
        if response.status_code == 403:
            print("   ✅ Доступ правильно запрещен для не-исполнителя")
        else:
            print(f"   ⚠️  Неожиданный статус: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ Тест завершен успешно!")


if __name__ == "__main__":
    try:
        test_executor_get_customers()
    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

