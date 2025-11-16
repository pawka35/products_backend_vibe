import requests
import json

BASE_URL = "http://localhost:8000"

def test_role_management():
    """Тест управления ролями (только для администраторов)"""
    
    print("Тест управления ролями FastAPI")
    print("=" * 50)
    
    # 1. Получение токена для администратора
    print("1. Получение токена для администратора...")
    admin_login = {
        "username": "admin",
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=admin_login)
    if response.status_code != 200:
        print(f"   Ошибка получения токена админа: {response.text}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   Токен администратора получен")
    
    # 2. Получение списка ролей
    print("\n2. Получение списка ролей...")
    response = requests.get(f"{BASE_URL}/api/admin/roles", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения ролей: {response.text}")
        return
    
    roles = response.json()
    print(f"   Найдено ролей: {len(roles)}")
    for role in roles:
        print(f"     - {role['name']}: {role['description']} (пользователей: {role['users_count']})")
    
    # 3. Создание новой роли
    print("\n3. Создание новой роли...")
    new_role_data = {
        "name": "moderator",
        "description": "Модератор системы",
        "permissions": "read,write,moderate"
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/roles", json=new_role_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка создания роли: {response.text}")
        return
    
    new_role = response.json()
    print(f"   Роль создана: {new_role['name']} (ID: {new_role['id']})")
    
    # 4. Получение информации о созданной роли
    print("\n4. Получение информации о созданной роли...")
    response = requests.get(f"{BASE_URL}/api/admin/roles/{new_role['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения роли: {response.text}")
        return
    
    role_info = response.json()
    print(f"   Роль: {role_info['name']}")
    print(f"   Описание: {role_info['description']}")
    print(f"   Разрешения: {role_info['permissions']}")
    
    # 5. Обновление роли
    print("\n5. Обновление роли...")
    update_data = {
        "description": "Обновленное описание модератора",
        "permissions": "read,write,moderate,delete"
    }
    
    response = requests.put(f"{BASE_URL}/api/admin/roles/{new_role['id']}", json=update_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка обновления роли: {response.text}")
        return
    
    updated_role = response.json()
    print(f"   Роль обновлена: {updated_role['description']}")
    
    # 6. Создание тестового пользователя для назначения роли
    print("\n6. Создание тестового пользователя...")
    user_data = {
        "username": "testmoderator",
        "email": "moderator@test.com",
        "password": "moderator123",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   Ошибка создания пользователя: {response.text}")
        return
    
    test_user = response.json()
    print(f"   Пользователь создан: {test_user['username']} (ID: {test_user['id']})")
    
    # 7. Назначение роли пользователю
    print("\n7. Назначение роли пользователю...")
    assignment_data = {
        "user_id": test_user['id'],
        "role_id": new_role['id']
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/roles/users/assign", json=assignment_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка назначения роли: {response.text}")
        return
    
    assignment = response.json()
    print(f"   Роль назначена: пользователь {test_user['username']} получил роль {new_role['name']}")
    
    # 8. Получение ролей пользователя
    print("\n8. Получение ролей пользователя...")
    response = requests.get(f"{BASE_URL}/api/admin/roles/users/{test_user['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения ролей пользователя: {response.text}")
        return
    
    user_roles = response.json()
    print(f"   Роли пользователя {test_user['username']}:")
    for role in user_roles:
        print(f"     - {role['name']}: {role['description']}")
    
    # 9. Получение пользователей по роли
    print("\n9. Получение пользователей по роли...")
    response = requests.get(f"{BASE_URL}/api/admin/roles/{new_role['id']}/users", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения пользователей по роли: {response.text}")
        return
    
    users_with_role = response.json()
    print(f"   Пользователи с ролью {new_role['name']}:")
    for user in users_with_role:
        print(f"     - {user['username']} ({user['email']})")
    
    # 10. Удаление назначения роли
    print("\n10. Удаление назначения роли...")
    response = requests.delete(f"{BASE_URL}/api/admin/roles/users/{assignment['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка удаления назначения роли: {response.text}")
        return
    
    print(f"   Назначение роли удалено")
    
    # 11. Проверка, что роль удалена у пользователя
    print("\n11. Проверка удаления роли...")
    response = requests.get(f"{BASE_URL}/api/admin/roles/users/{test_user['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения ролей пользователя: {response.text}")
        return
    
    user_roles_after = response.json()
    print(f"   Роли пользователя после удаления: {len(user_roles_after)}")
    
    # 12. Деактивация роли
    print("\n12. Деактивация роли...")
    deactivate_data = {"is_active": False}
    response = requests.patch(f"{BASE_URL}/api/admin/roles/{new_role['id']}", json=deactivate_data, headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка деактивации роли: {response.text}")
        return
    
    deactivated_role = response.json()
    print(f"   Роль деактивирована: {deactivated_role['is_active']}")
    
    # 13. Проверка фильтрации активных ролей
    print("\n13. Проверка фильтрации активных ролей...")
    response = requests.get(f"{BASE_URL}/api/admin/roles/?active_only=true", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения активных ролей: {response.text}")
        return
    
    active_roles = response.json()
    print(f"   Активных ролей: {len(active_roles)}")
    
    # 14. Проверка всех ролей (включая неактивные)
    response = requests.get(f"{BASE_URL}/api/admin/roles/?active_only=false", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения всех ролей: {response.text}")
        return
    
    all_roles = response.json()
    print(f"   Всего ролей: {len(all_roles)}")
    
    print("\n" + "=" * 50)
    print("Тест управления ролями завершен успешно! 🎉")

def test_role_permissions():
    """Тест разрешений для управления ролями"""
    
    print("\nТест разрешений для управления ролями")
    print("=" * 50)
    
    # 1. Создание обычного пользователя
    print("1. Создание обычного пользователя...")
    user_data = {
        "username": "regularuser",
        "email": "regular@test.com",
        "password": "regular123",
        "role": "customer"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"   Ошибка создания пользователя: {response.text}")
        return
    
    regular_user = response.json()
    print(f"   Пользователь создан: {regular_user['username']}")
    
    # 2. Получение токена для обычного пользователя
    print("\n2. Получение токена для обычного пользователя...")
    login_data = {
        "username": "regularuser",
        "password": "regular123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if response.status_code != 200:
        print(f"   Ошибка получения токена: {response.text}")
        return
    
    user_token = response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("   Токен получен")
    
    # 3. Попытка доступа к управлению ролями (должна быть запрещена)
    print("\n3. Попытка доступа к управлению ролями...")
    
    # Попытка получить список ролей
    response = requests.get(f"{BASE_URL}/api/admin/roles/", headers=user_headers)
    if response.status_code == 403:
        print("   ✅ Доступ к /admin/roles/ запрещен для обычного пользователя")
    else:
        print(f"   ❌ Неожиданный статус: {response.status_code}")
    
    # Попытка создать роль
    role_data = {"name": "test", "description": "test"}
    response = requests.post(f"{BASE_URL}/api/admin/roles/", json=role_data, headers=user_headers)
    if response.status_code == 403:
        print("   ✅ Создание ролей запрещено для обычного пользователя")
    else:
        print(f"   ❌ Неожиданный статус: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("Тест разрешений завершен успешно! 🎉")

if __name__ == "__main__":
    test_role_management()
    test_role_permissions()
