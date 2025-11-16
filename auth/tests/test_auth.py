import requests
import json

BASE_URL = "http://localhost:8000"

# Список созданных пользователей для очистки
created_user_ids = []

def cleanup_users():
    """Удалить всех созданных тестовых пользователей"""
    if not created_user_ids:
        return
    
    print(f"\n🧹 Очистка тестовых данных ({len(created_user_ids)} пользователей)...")
    
    # Получаем токен администратора
    admin_login = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=admin_login)
    if response.status_code != 200:
        print("❌ Не удалось получить токен администратора для очистки")
        return
    
    admin_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    deleted_count = 0
    for user_id in created_user_ids:
        response = requests.delete(
            f"{BASE_URL}/api/admin/users/{user_id}",
            headers=headers
        )
        if response.status_code in [200, 204]:
            deleted_count += 1
    
    print(f"✅ Удалено {deleted_count} из {len(created_user_ids)} пользователей")
    created_user_ids.clear()

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
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   Ошибка регистрации: {response.text}")
        return
    
    user = response.json()
    print(f"   Пользователь создан: {user['username']}")
    created_user_ids.append(user['id'])  # Сохраняем для очистки
    
    # 2. Получение токена
    print("\n2. Получение токена...")
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if response.status_code != 200:
        print(f"   Ошибка получения токена: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Токен получен")
    
    # 3. Тест защищенного эндпоинта
    print("\n3. Тест защищенного эндпоинта...")
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code != 200:
        print(f"   Ошибка доступа к /auth/me: {response.text}")
        return
    
    user_info = response.json()
    print(f"   Получена информация о пользователе: {user_info['username']}")
    
    print("\n" + "=" * 50)
    print("Тест завершен успешно! 🎉")
    
    # Очистка
    cleanup_users()

def test_user_profile_update():
    """Тест обновления профиля и пароля пользователя"""
    
    print("\nТест обновления профиля пользователя")
    print("=" * 50)
    
    # 1. Создаем тестового пользователя
    print("1. Создание тестового пользователя...")
    import random
    test_suffix = random.randint(1000, 9999)
    user_data = {
        "username": f"profiletest_{test_suffix}",
        "email": f"profiletest_{test_suffix}@example.com",
        "password": "TestPass123!",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   Ошибка регистрации: {response.text}")
        return
    
    user = response.json()
    print(f"   Пользователь создан: {user_data['username']}")
    created_user_ids.append(user['id'])  # Сохраняем для очистки
    
    # 2. Получаем токен
    print("\n2. Получение токена...")
    login_data = {
        "username": user_data['username'],
        "password": user_data['password']
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if response.status_code != 200:
        print(f"   Ошибка получения токена: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   Токен получен")
    
    # 3. Обновляем username
    print("\n3. Обновление username...")
    new_username = f"updated_{test_suffix}"
    update_data = {
        "username": new_username
    }
    
    response = requests.put(f"{BASE_URL}/api/auth/me", json=update_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   Username обновлен: {result['user']['username']}")
    else:
        print(f"   Ошибка обновления username: {response.text}")
    
    # 4. Обновляем email
    print("\n4. Обновление email...")
    new_email = f"updated_{test_suffix}@example.com"
    update_data = {
        "email": new_email
    }
    
    response = requests.put(f"{BASE_URL}/api/auth/me", json=update_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   Email обновлен: {result['user']['email']}")
    else:
        print(f"   Ошибка обновления email: {response.text}")
    
    # 5. Обновляем и username и email одновременно
    print("\n5. Обновление username и email одновременно...")
    new_username2 = f"updated2_{test_suffix}"
    new_email2 = f"updated2_{test_suffix}@example.com"
    update_data = {
        "username": new_username2,
        "email": new_email2
    }
    
    response = requests.put(f"{BASE_URL}/api/auth/me", json=update_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   Оба поля обновлены:")
        print(f"   - Username: {result['user']['username']}")
        print(f"   - Email: {result['user']['email']}")
    else:
        print(f"   Ошибка обновления: {response.text}")
    
    # 6. Попытка обновить без указания полей (должна быть ошибка)
    print("\n6. Попытка обновления без указания полей...")
    response = requests.put(f"{BASE_URL}/api/auth/me", json={}, headers=headers)
    if response.status_code == 400:
        print(f"   Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"   Неожиданный результат: {response.status_code}")
    
    # 7. Изменение пароля
    print("\n7. Изменение пароля...")
    password_data = {
        "current_password": "TestPass123!",
        "new_password": "NewTestPass456!"
    }
    
    response = requests.put(f"{BASE_URL}/api/auth/me/password", json=password_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"   Пароль изменен успешно: {result['message']}")
    else:
        print(f"   Ошибка изменения пароля: {response.text}")
    
    # 8. Проверяем вход со старым паролем (должно быть отклонено)
    print("\n8. Попытка входа со старым паролем...")
    old_login_data = {
        "username": new_username2,
        "password": "TestPass123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=old_login_data)
    if response.status_code == 401:
        print("   Правильно: вход со старым паролем отклонен")
    else:
        print(f"   Неожиданный результат: {response.status_code}")
    
    # 9. Проверяем вход с новым паролем
    print("\n9. Вход с новым паролем...")
    new_login_data = {
        "username": new_username2,
        "password": "NewTestPass456!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=new_login_data)
    if response.status_code == 200:
        print("   Вход с новым паролем успешен")
        new_token = response.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        
        # Проверяем профиль с новым токеном
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=new_headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"   Профиль получен: {user_info['username']}")
        
        # 10. Попытка изменить пароль с неверным текущим паролем
        print("\n10. Попытка изменения пароля с неверным текущим паролем...")
        wrong_password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "AnotherPass789!"
        }
        
        response = requests.put(f"{BASE_URL}/api/auth/me/password", json=wrong_password_data, headers=new_headers)
        if response.status_code == 400:
            print(f"   Ожидаемая ошибка: {response.json()['detail']}")
        else:
            print(f"   Неожиданный результат: {response.status_code}")
    else:
        print(f"   Ошибка входа: {response.text}")
        print("   Пропускаем тест 10 из-за неудачного входа")
    
    print("\n" + "=" * 50)
    print("Тест обновления профиля завершен успешно! 🎉")
    
    # Очистка
    cleanup_users()

if __name__ == "__main__":
    try:
        test_auth_flow()
        print("\n")
        test_user_profile_update()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
        cleanup_users()
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        cleanup_users()
        raise
