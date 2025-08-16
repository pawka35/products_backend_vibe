import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_flow():
    """Тест основных API функций"""
    
    print("Тест API FastAPI")
    print("=" * 50)
    
    # 1. Проверка здоровья сервиса
    print("1. Проверка здоровья сервиса...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code != 200:
        print(f"   Ошибка health check: {response.text}")
        return
    
    health = response.json()
    print(f"   Статус: {health['status']}")
    
    # 2. Проверка главной страницы
    print("\n2. Проверка главной страницы...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code != 200:
        print(f"   Ошибка главной страницы: {response.text}")
        return
    
    root = response.json()
    print(f"   Сообщение: {root['message']}")
    print(f"   Документация: {root['docs']}")
    
    # 3. Регистрация пользователя
    print("\n3. Регистрация пользователя...")
    user_data = {
        "username": "apitestuser",
        "email": "apitest@example.com",
        "password": "apitest123",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   Ошибка регистрации: {response.text}")
        return
    
    user = response.json()
    print(f"   Пользователь создан: {user['username']}")
    
    # 4. Получение токена
    print("\n4. Получение токена...")
    login_data = {
        "username": "apitestuser",
        "password": "apitest123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    if response.status_code != 200:
        print(f"   Ошибка получения токена: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Токен получен")
    
    # 5. Тест защищенных эндпоинтов
    print("\n5. Тест защищенных эндпоинтов...")
    
    # 5.1 Проверка /auth/me
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code != 200:
        print(f"     Ошибка /auth/me: {response.text}")
    else:
        print("     /auth/me работает")
    
    # 5.2 Проверка /users/
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    if response.status_code != 200:
        print(f"     Ошибка /users/: {response.text}")
    else:
        users = response.json()
        print(f"     /users/ работает, найдено пользователей: {len(users)}")
    
    # 5.3 Проверка /users/{user_id}
    response = requests.get(f"{BASE_URL}/users/{user['id']}", headers=headers)
    if response.status_code != 200:
        print(f"     Ошибка /users/{user['id']}: {response.text}")
    else:
        print("     /users/{user_id} работает")
    
    print("\n" + "=" * 50)
    print("Тест API завершен успешно! 🎉")

if __name__ == "__main__":
    test_api_flow()
