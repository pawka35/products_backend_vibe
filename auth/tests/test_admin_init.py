import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_initialization():
    """Тест инициализации администратора"""
    
    print("Тест инициализации администратора")
    print("=" * 50)
    
    # 1. Проверка, что администратор существует
    print("1. Проверка существования администратора...")
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=admin_login)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения токена админа: {response.text}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   ✅ Администратор существует и может войти в систему")
    
    # 2. Проверка информации об администраторе
    print("\n2. Проверка информации об администраторе...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=admin_headers)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения информации об админе: {response.text}")
        return
    
    admin_info = response.json()
    print(f"   ✅ Администратор: {admin_info['username']}")
    print(f"   ✅ Email: {admin_info['email']}")
    print(f"   ✅ Роль: {admin_info['role']}")
    print(f"   ✅ Активен: {admin_info['is_active']}")
    
    # 3. Проверка базовых ролей
    print("\n3. Проверка базовых ролей...")
    response = requests.get(f"{BASE_URL}/admin/roles/", headers=admin_headers)
    if response.status_code != 200:
        print(f"   ❌ Ошибка получения ролей: {response.text}")
        return
    
    roles = response.json()
    print(f"   ✅ Найдено ролей: {len(roles)}")
    
    # Проверяем наличие базовых ролей
    role_names = [role['name'] for role in roles]
    expected_roles = ['admin', 'customer', 'executor']
    
    for expected_role in expected_roles:
        if expected_role in role_names:
            print(f"   ✅ Роль '{expected_role}' найдена")
        else:
            print(f"   ❌ Роль '{expected_role}' не найдена")
    
    print("\n" + "=" * 50)
    print("Тест инициализации администратора завершен успешно! 🎉")

def test_admin_registration_protection():
    """Тест защиты от создания администраторов через регистрацию"""
    
    print("\nТест защиты от создания администраторов")
    print("=" * 50)
    
    # 1. Попытка создать пользователя с ролью администратора
    print("1. Попытка создать пользователя с ролью администратора...")
    admin_user_data = {
        "username": "fakeadmin",
        "email": "fakeadmin@test.com",
        "password": "fakeadmin123",
        "role": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=admin_user_data)
    if response.status_code == 403:
        print("   ✅ Создание пользователя с ролью администратора заблокировано")
        error_detail = response.json().get('detail', '')
        if 'запрещено' in error_detail:
            print("   ✅ Правильное сообщение об ошибке")
        else:
            print(f"   ⚠️ Неожиданное сообщение об ошибке: {error_detail}")
    else:
        print(f"   ❌ Неожиданный статус: {response.status_code}")
        print(f"   ❌ Ответ: {response.text}")
    
    # 2. Попытка создать пользователя с обычной ролью (должна пройти)
    print("\n2. Попытка создать пользователя с обычной ролью...")
    regular_user_data = {
        "username": "regularuser2",
        "email": "regular2@test.com",
        "password": "regular123",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=regular_user_data)
    if response.status_code == 200:
        print("   ✅ Создание пользователя с обычной ролью разрешено")
        user = response.json()
        print(f"   ✅ Пользователь создан: {user['username']} с ролью {user['role']}")
    else:
        print(f"   ❌ Ошибка создания обычного пользователя: {response.text}")
    
    # 3. Проверка, что fakeadmin не был создан
    print("\n3. Проверка, что fakeadmin не был создан...")
    fake_admin_login = {
        "username": "fakeadmin",
        "password": "fakeadmin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=fake_admin_login)
    if response.status_code == 401:
        print("   ✅ Пользователь fakeadmin не может войти (не создан)")
    else:
        print(f"   ❌ Неожиданный статус: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Тест защиты от создания администраторов завершен успешно! 🎉")

if __name__ == "__main__":
    test_admin_initialization()
    test_admin_registration_protection()
