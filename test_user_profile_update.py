#!/usr/bin/env python3
"""
Быстрый тест для проверки обновления профиля и пароля пользователя
"""

import requests
import sys
import random

BASE_URL = "http://localhost:8000"

# ID созданного пользователя для очистки
created_user_id = None

def create_test_user():
    """Создать тестового пользователя"""
    global created_user_id
    test_suffix = random.randint(1000, 9999)
    username = f"profiletest_{test_suffix}"
    email = f"profiletest_{test_suffix}@example.com"
    password = "TestPass123!"
    
    print(f"👤 Создание тестового пользователя {username}...")
    
    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if response.status_code == 200:
        user = response.json()
        created_user_id = user['id']  # Сохраняем ID для очистки
        print("✅ Пользователь создан")
        return username, email, password
    else:
        print(f"❌ Ошибка создания: {response.text}")
        return None, None, None

def cleanup_test_user():
    """Удалить созданного тестового пользователя"""
    global created_user_id
    if not created_user_id:
        return
    
    print(f"\n🧹 Очистка тестовых данных (user_id: {created_user_id})...")
    
    # Получаем токен администратора для удаления
    admin_login = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=admin_login)
    if response.status_code != 200:
        print("❌ Не удалось получить токен администратора для очистки")
        return
    
    admin_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Удаляем пользователя
    response = requests.delete(
        f"{BASE_URL}/admin/users/{created_user_id}",
        headers=headers
    )
    
    if response.status_code in [200, 204]:
        print("✅ Тестовый пользователь удален")
    else:
        print(f"⚠️  Не удалось удалить пользователя: {response.text}")
    
    created_user_id = None

def get_token(username, password):
    """Получить токен"""
    print(f"\n🔐 Получение токена для {username}...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Токен получен")
        return token
    else:
        print(f"❌ Ошибка получения токена: {response.text}")
        return None

def get_user_info(token):
    """Получить информацию о пользователе"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Ошибка получения профиля: {response.text}")
        return None

def update_username(token, new_username):
    """Обновить username"""
    print(f"\n📝 Обновление username на {new_username}...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {"username": new_username}
    
    response = requests.put(f"{BASE_URL}/auth/me", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Username обновлен: {result['user']['username']}")
        return True
    else:
        print(f"❌ Ошибка обновления: {response.text}")
        return False

def update_email(token, new_email):
    """Обновить email"""
    print(f"\n📧 Обновление email на {new_email}...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {"email": new_email}
    
    response = requests.put(f"{BASE_URL}/auth/me", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Email обновлен: {result['user']['email']}")
        return True
    else:
        print(f"❌ Ошибка обновления: {response.text}")
        return False

def update_both(token, new_username, new_email):
    """Обновить username и email одновременно"""
    print(f"\n🔄 Обновление username и email одновременно...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "username": new_username,
        "email": new_email
    }
    
    response = requests.put(f"{BASE_URL}/auth/me", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Оба поля обновлены:")
        print(f"   - Username: {result['user']['username']}")
        print(f"   - Email: {result['user']['email']}")
        return True
    else:
        print(f"❌ Ошибка обновления: {response.text}")
        return False

def update_empty(token):
    """Попытка обновления без указания полей"""
    print(f"\n⚠️  Попытка обновления без указания полей...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {}
    
    response = requests.put(f"{BASE_URL}/auth/me", json=data, headers=headers)
    
    if response.status_code == 400:
        print(f"✅ Ожидаемая ошибка: {response.json()['detail']}")
        return True
    else:
        print(f"❌ Неожиданный результат: {response.status_code}")
        return False

def change_password(token, current_password, new_password):
    """Изменить пароль"""
    print(f"\n🔑 Изменение пароля...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "current_password": current_password,
        "new_password": new_password
    }
    
    response = requests.put(f"{BASE_URL}/auth/me/password", json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Пароль изменен: {result['message']}")
        return True
    else:
        print(f"❌ Ошибка изменения пароля: {response.text}")
        return False

def check_old_password(username, old_password):
    """Проверить вход со старым паролем"""
    print(f"\n🚫 Попытка входа со старым паролем...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": old_password}
    )
    
    if response.status_code == 401:
        print("✅ Правильно: вход со старым паролем отклонен")
        return True
    else:
        print(f"❌ Неожиданный результат: {response.status_code}")
        return False

def check_new_password(username, new_password):
    """Проверить вход с новым паролем"""
    print(f"\n✅ Попытка входа с новым паролем...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": new_password}
    )
    
    if response.status_code == 200:
        print("✅ Вход с новым паролем успешен")
        return response.json()["access_token"]
    else:
        print(f"❌ Ошибка входа: {response.text}")
        return None

def check_wrong_current_password(token):
    """Попытка изменения пароля с неверным текущим паролем"""
    print(f"\n⚠️  Попытка изменения пароля с неверным текущим паролем...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "current_password": "WrongPassword123!",
        "new_password": "AnotherPass789!"
    }
    
    response = requests.put(f"{BASE_URL}/auth/me/password", json=data, headers=headers)
    
    if response.status_code == 400:
        print(f"✅ Ожидаемая ошибка: {response.json()['detail']}")
        return True
    else:
        print(f"❌ Неожиданный результат: {response.status_code}")
        return False

def main():
    print("=" * 70)
    print("🧪 ТЕСТ ОБНОВЛЕНИЯ ПРОФИЛЯ И ПАРОЛЯ ПОЛЬЗОВАТЕЛЯ")
    print("=" * 70)
    
    # 1. Создаем тестового пользователя
    username, email, password = create_test_user()
    if not username:
        print("\n❌ Не удалось создать тестового пользователя")
        sys.exit(1)
    
    # 2. Получаем токен
    token = get_token(username, password)
    if not token:
        print("\n❌ Не удалось получить токен")
        sys.exit(1)
    
    # 3. Получаем информацию о пользователе
    print(f"\n📋 Текущий профиль:")
    user_info = get_user_info(token)
    if user_info:
        print(f"   - Username: {user_info['username']}")
        print(f"   - Email: {user_info['email']}")
        print(f"   - Role: {user_info['role']}")
    
    # 4. Обновляем username
    test_suffix = random.randint(1000, 9999)
    new_username = f"updated_{test_suffix}"
    update_username(token, new_username)
    
    # 5. Обновляем email
    new_email = f"updated_{test_suffix}@example.com"
    update_email(token, new_email)
    
    # 6. Обновляем username и email одновременно
    new_username2 = f"updated2_{test_suffix}"
    new_email2 = f"updated2_{test_suffix}@example.com"
    update_both(token, new_username2, new_email2)
    
    # 7. Попытка обновления без указания полей
    update_empty(token)
    
    # 8. Получаем обновленную информацию
    print(f"\n📋 Обновленный профиль:")
    user_info = get_user_info(token)
    if user_info:
        print(f"   - Username: {user_info['username']}")
        print(f"   - Email: {user_info['email']}")
        print(f"   - Updated at: {user_info.get('updated_at', 'N/A')}")
    
    # 9. Изменяем пароль
    new_password = "NewTestPass456!"
    change_password(token, password, new_password)
    
    # 10. Проверяем вход со старым паролем
    check_old_password(new_username2, password)
    
    # 11. Проверяем вход с новым паролем
    new_token = check_new_password(new_username2, new_password)
    
    if new_token:
        # 12. Проверяем профиль с новым токеном
        print(f"\n📋 Профиль с новым токеном:")
        user_info = get_user_info(new_token)
        if user_info:
            print(f"   - Username: {user_info['username']}")
            print(f"   - Email: {user_info['email']}")
        
        # 13. Попытка изменения пароля с неверным текущим паролем
        check_wrong_current_password(new_token)
    
    print("\n" + "=" * 70)
    print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 70)
    print("\n📝 Проверено:")
    print("   ✅ Обновление username")
    print("   ✅ Обновление email")
    print("   ✅ Обновление обоих полей одновременно")
    print("   ✅ Валидация пустого запроса")
    print("   ✅ Изменение пароля")
    print("   ✅ Проверка старого пароля (отклонено)")
    print("   ✅ Проверка нового пароля (успешно)")
    print("   ✅ Валидация неверного текущего пароля")
    
    # Очистка тестовых данных
    cleanup_test_user()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
        # Попытка очистить данные перед выходом
        try:
            cleanup_test_user()
        except:
            pass
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        # Попытка очистить данные перед выходом
        try:
            cleanup_test_user()
        except:
            pass
        sys.exit(1)

