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
        "password": "Admin123!"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/token", data=admin_login)
    if response.status_code != 200:
        print(f"   Ошибка получения токена админа: {response.text}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("   Токен администратора получен")
    
    # 2. Получение статистики пользователей
    print("\n2. Получение статистики пользователей...")
    response = requests.get(f"{BASE_URL}/api/admin/statistics", headers=admin_headers)
    if response.status_code != 200:
        print(f"   Ошибка получения статистики: {response.text}")
        return
    
    stats = response.json()
    print(f"   Всего пользователей: {stats['total_users']}")
    print(f"   По ролям: {stats['users_by_role']}")
    
    # 3. Получение списка всех пользователей
    print("\n3. Получение списка всех пользователей...")
    response = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
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
                f"{BASE_URL}/api/admin/users/{test_user['id']}/role",
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
            f"{BASE_URL}/api/admin/users/{test_user['id']}/password",
            json=password_data,
            headers=admin_headers
        )
        
        if response.status_code != 200:
            print(f"     Ошибка изменения пароля: {response.text}")
        else:
            print(f"     Пароль пользователя {test_user['username']} изменен")
    
        # 6. Проверка, что изменения применились
        print("\n6. Проверка изменений...")
        response = requests.get(f"{BASE_URL}/api/admin/users/{test_user['id']}", headers=admin_headers)
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
        
        response = requests.post(f"{BASE_URL}/api/auth/token", data=new_login)
        if response.status_code != 200:
            print(f"   Ошибка входа с новым паролем: {response.text}")
        else:
            print("   Вход с новым паролем успешен")
    else:
        print("   Пользователь testuser не найден, пропускаем тесты 6-7")
    
    print("\n" + "=" * 50)
    print("Тест завершен успешно! 🎉")

def test_admin_create_user():
    """Тест создания пользователя администратором"""
    
    print("\nТест создания пользователя администратором")
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
    
    # 2. Создание пользователя с ролью customer
    print("\n2. Создание пользователя с ролью customer...")
    customer_data = {
        "username": "new_customer",
        "email": "customer@example.com",
        "password": "SecurePass123!",
        "role": "customer"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        json=customer_data,
        headers=admin_headers
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"   Пользователь создан: {user['username']} (роль: {user['role']})")
        customer_id = user['id']
    else:
        print(f"   Ошибка создания пользователя: {response.text}")
        customer_id = None
    
    # 3. Создание пользователя с ролью executor
    print("\n3. Создание пользователя с ролью executor...")
    executor_data = {
        "username": "new_executor",
        "email": "executor@example.com",
        "password": "SecurePass123!",
        "role": "executor"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        json=executor_data,
        headers=admin_headers
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"   Пользователь создан: {user['username']} (роль: {user['role']})")
        executor_id = user['id']
    else:
        print(f"   Ошибка создания пользователя: {response.text}")
        executor_id = None
    
    # 4. Создание пользователя с ролью admin
    print("\n4. Создание пользователя с ролью admin...")
    admin_data = {
        "username": "new_admin",
        "email": "newadmin@example.com",
        "password": "SecurePass123!",
        "role": "admin"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        json=admin_data,
        headers=admin_headers
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"   Пользователь создан: {user['username']} (роль: {user['role']})")
        new_admin_id = user['id']
    else:
        print(f"   Ошибка создания пользователя: {response.text}")
        new_admin_id = None
    
    # 5. Попытка создания пользователя с существующим username
    print("\n5. Попытка создания пользователя с существующим username...")
    duplicate_data = {
        "username": "new_customer",
        "email": "another@example.com",
        "password": "SecurePass123!",
        "role": "customer"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        json=duplicate_data,
        headers=admin_headers
    )
    
    if response.status_code == 400:
        print(f"   Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"   Неожиданный результат: {response.status_code}")
    
    # 6. Попытка создания пользователя с существующим email
    print("\n6. Попытка создания пользователя с существующим email...")
    duplicate_email_data = {
        "username": "another_user",
        "email": "customer@example.com",
        "password": "SecurePass123!",
        "role": "customer"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        json=duplicate_email_data,
        headers=admin_headers
    )
    
    if response.status_code == 400:
        print(f"   Ожидаемая ошибка: {response.json()['detail']}")
    else:
        print(f"   Неожиданный результат: {response.status_code}")
    
    # 7. Проверка, что новый администратор может войти
    if new_admin_id:
        print("\n7. Проверка входа нового администратора...")
        new_admin_login = {
            "username": "new_admin",
            "password": "SecurePass123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/token", data=new_admin_login)
        if response.status_code == 200:
            print("   Новый администратор успешно вошел в систему")
            new_admin_token = response.json()["access_token"]
            
            # Проверка, что новый админ может создавать пользователей
            print("\n8. Проверка прав нового администратора...")
            new_admin_headers = {"Authorization": f"Bearer {new_admin_token}"}
            
            test_user_data = {
                "username": "test_by_new_admin",
                "email": "testbynewadmin@example.com",
                "password": "SecurePass123!",
                "role": "customer"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/admin/users",
                json=test_user_data,
                headers=new_admin_headers
            )
            
            if response.status_code == 200:
                print("   Новый администратор может создавать пользователей")
            else:
                print(f"   Ошибка: {response.text}")
        else:
            print(f"   Ошибка входа: {response.text}")
    
    # 8. Получение статистики
    print("\n9. Получение обновленной статистики...")
    response = requests.get(f"{BASE_URL}/api/admin/statistics", headers=admin_headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"   Всего пользователей: {stats['total_users']}")
        print(f"   По ролям: {stats['users_by_role']}")
    
    print("\n" + "=" * 50)
    print("Тест создания пользователей завершен успешно! 🎉")

if __name__ == "__main__":
    test_admin_functions()
    print("\n")
    test_admin_create_user()
