import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_functions():
    """Тест административных функций FastAPI"""
    
    print("Тест административных функций FastAPI")
    print("=" * 50)
    
    # 1. Сначала получим токен для админа
    print("1. Получение токена для администратора...")
    admin_login = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=admin_login)
    if response.status_code != 200:
        print(f"   Ошибка получения токена админа: {response.text}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   Токен администратора получен")
    
    # 2. Получение статистики пользователей
    print("\n2. Получение статистики пользователей...")
    response = requests.get(f"{BASE_URL}/admin/statistics", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения статистики: {response.text}")
        return
    
    stats = response.json()
    print(f"   Всего пользователей: {stats['total_users']}")
    print(f"   По ролям: {stats['users_by_role']}")
    
    # 3. Получение списка всех пользователей
    print("\n3. Получение списка всех пользователей...")
    response = requests.get(f"{BASE_URL}/admin/users", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения пользователей: {response.text}")
        return
    
    users = response.json()
    print(f"   Найдено пользователей: {len(users)}")
    
    # 4. Изменение роли пользователя testuser
    print("\n4. Изменение роли пользователя testuser...")
    if len(users) > 1:  # Предполагаем, что есть хотя бы один пользователь кроме админа
        test_user = None
        for user in users:
            if user['username'] == 'testuser':
                test_user = user
                break
        
        if test_user:
            role_data = {"new_role": "executor"}
            response = requests.put(
                f"{BASE_URL}/admin/users/{test_user['id']}/role",
                json=role_data,
                headers=admin_headers
            )
            
            if response.status_code != 200:
                print(f"     Ошибка изменения роли: {response.text}")
            else:
                print(f"     Роль пользователя {test_user['username']} изменена на executor")
        else:
            print("     Пользователь testuser не найден")
    
    # 5. Изменение пароля пользователя testuser
    print("\n5. Изменение пароля пользователя testuser...")
    if test_user:
        password_data = {"new_password": "newpassword123"}
        response = requests.put(
            f"{BASE_URL}/admin/users/{test_user['id']}/password",
            json=password_data,
            headers=admin_headers
        )
        
        if response.status_code != 200:
            print(f"     Ошибка изменения пароля: {response.text}")
        else:
            print(f"     Пароль пользователя {test_user['username']} изменен")
    
    # 6. Проверка, что изменения применились
    print("\n6. Проверка изменений...")
    response = requests.get(f"{BASE_URL}/admin/users/{test_user['id']}", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения пользователя: {response.text}")
        return
    
    updated_user = response.json()
    print(f"   Обновленная роль: {updated_user['role']}")
    
    # 7. Тест с новым паролем
    print("\n7. Тест с новым паролем...")
    new_login = {
        "username": "testuser",
        "password": "newpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=new_login)
    if response.status_code != 200:
        print(f"   Ошибка входа с новым паролем: {response.text}")
    else:
        print("   Вход с новым паролем успешен")
    
    print("\n" + "=" * 50)
    print("Тест завершен успешно! 🎉")

if __name__ == "__main__":
    test_admin_functions()
