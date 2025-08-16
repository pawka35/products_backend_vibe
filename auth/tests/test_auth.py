import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """Тест полного цикла аутентификации"""
    
    print("Тест аутентификации FastAPI")
    print("=" * 50)
    
    # 1. Регистрация
    print("1. Регистрация пользователя...")
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   Ошибка регистрации: {response.text}")
        return
    
    user = response.json()
    print(f"   Пользователь создан: {user['username']}")
    
    # 2. Получение токена
    print("\n2. Получение токена...")
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    if response.status_code != 200:
        print(f"   Ошибка получения токена: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Токен получен")
    
    # 3. Тест защищенного эндпоинта
    print("\n3. Тест защищенного эндпоинта...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code != 200:
        print(f"   Ошибка доступа к /auth/me: {response.text}")
        return
    
    user_info = response.json()
    print(f"   Получена информация о пользователе: {user_info['username']}")
    
    print("\n" + "=" * 50)
    print("Тест завершен успешно! 🎉")

if __name__ == "__main__":
    test_auth_flow()
