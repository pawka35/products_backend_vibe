#!/usr/bin/env python3
"""
Простой тест для проверки функциональности ролей
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_role_functionality():
    """Тест функциональности ролей"""
    
    print("Тест функциональности ролей")
    print("=" * 50)
    
    # 1. Получение токена для администратора
    print("1. Получение токена для администратора...")
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/token", data=admin_login)
        if response.status_code != 200:
            print(f"   ❌ Ошибка получения токена админа: {response.text}")
            return False
        
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("   ✅ Токен администратора получен")
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Не удается подключиться к серверу. Убедитесь, что проект запущен.")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # 2. Проверка основных эндпоинтов
    print("\n2. Проверка основных эндпоинтов...")
    
    # Проверка главной страницы
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("   ✅ Главная страница работает")
        else:
            print(f"   ❌ Главная страница: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка главной страницы: {e}")
    
    # Проверка /auth/me
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ /auth/me работает: {user_info['username']} ({user_info['role']})")
        else:
            print(f"   ❌ /auth/me: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка /auth/me: {e}")
    
    # Проверка /users
    try:
        response = requests.get(f"{BASE_URL}/users/", headers=admin_headers)
        if response.status_code == 200:
            users = response.json()
            print(f"   ✅ /users работает: {len(users)} пользователей")
        else:
            print(f"   ❌ /users: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Ошибка /users: {e}")
    
    print("\n" + "=" * 50)
    print("Тест завершен! 🎉")
    print("\nДля полного тестирования ролей:")
    print("1. Запустите проект: python main.py")
    print("2. В другом терминале запустите: python auth/tests/test_roles.py")
    
    return True

if __name__ == "__main__":
    test_role_functionality()
