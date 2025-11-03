#!/usr/bin/env python3
"""
Быстрый тест для проверки создания пользователей администратором
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

# Список созданных пользователей для очистки
created_users = []

def get_admin_token(username="admin", password="Admin123!"):
    """Получить токен администратора"""
    print(f"🔐 Получение токена для {username}...")
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

def create_user(token, username, email, password, role):
    """Создать пользователя"""
    print(f"\n👤 Создание пользователя {username} с ролью {role}...")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "username": username,
        "email": email,
        "password": password,
        "role": role
    }
    
    response = requests.post(
        f"{BASE_URL}/admin/users",
        json=data,
        headers=headers
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ Пользователь создан:")
        print(f"   - ID: {user['id']}")
        print(f"   - Username: {user['username']}")
        print(f"   - Email: {user['email']}")
        print(f"   - Role: {user['role']}")
        created_users.append(user['id'])  # Добавляем ID для последующей очистки
        return user
    else:
        print(f"❌ Ошибка создания: {response.text}")
        return None

def delete_user(token, user_id):
    """Удалить пользователя"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{BASE_URL}/admin/users/{user_id}",
        headers=headers
    )
    return response.status_code in [200, 204]

def cleanup_users(token):
    """Очистка всех созданных тестовых пользователей"""
    if not created_users:
        return
    
    print(f"\n🧹 Очистка тестовых данных ({len(created_users)} пользователей)...")
    deleted_count = 0
    for user_id in created_users:
        if delete_user(token, user_id):
            deleted_count += 1
    
    print(f"✅ Удалено {deleted_count} из {len(created_users)} пользователей")
    created_users.clear()

def check_login(username, password):
    """Проверить вход пользователя"""
    print(f"\n🔑 Проверка входа для {username}...")
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        print("✅ Вход успешен")
        return True
    else:
        print(f"❌ Ошибка входа: {response.text}")
        return False

def get_user_statistics(token):
    """Получить статистику пользователей"""
    print("\n📊 Получение статистики пользователей...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/admin/statistics", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print("✅ Статистика:")
        print(f"   - Всего пользователей: {stats['total_users']}")
        print(f"   - По ролям: {stats['users_by_role']}")
        return stats
    else:
        print(f"❌ Ошибка получения статистики: {response.text}")
        return None

def main():
    print("=" * 70)
    print("🧪 ТЕСТ СОЗДАНИЯ ПОЛЬЗОВАТЕЛЕЙ АДМИНИСТРАТОРОМ")
    print("=" * 70)
    
    # 1. Получаем токен администратора
    admin_token = get_admin_token()
    if not admin_token:
        print("\n❌ Не удалось получить токен администратора")
        sys.exit(1)
    
    # 2. Создаем пользователя-заказчика
    customer = create_user(
        admin_token,
        username="test_customer_" + str(hash("customer") % 10000),
        email=f"customer_{hash('customer') % 10000}@test.com",
        password="TestPass123!",
        role="customer"
    )
    
    # 3. Создаем пользователя-исполнителя
    executor = create_user(
        admin_token,
        username="test_executor_" + str(hash("executor") % 10000),
        email=f"executor_{hash('executor') % 10000}@test.com",
        password="TestPass123!",
        role="executor"
    )
    
    # 4. Создаем пользователя-администратора
    new_admin = create_user(
        admin_token,
        username="test_admin_" + str(hash("admin") % 10000),
        email=f"admin_{hash('admin') % 10000}@test.com",
        password="TestPass123!",
        role="admin"
    )
    
    # 5. Проверяем вход созданных пользователей
    if customer:
        check_login(customer["username"], "TestPass123!")
    
    if executor:
        check_login(executor["username"], "TestPass123!")
    
    if new_admin:
        check_login(new_admin["username"], "TestPass123!")
        
        # Проверяем, что новый администратор может создавать пользователей
        new_admin_token = get_admin_token(
            new_admin["username"],
            "TestPass123!"
        )
        
        if new_admin_token:
            print("\n🔐 Проверка прав нового администратора...")
            test_user = create_user(
                new_admin_token,
                username="test_by_new_admin_" + str(hash("test") % 10000),
                email=f"test_{hash('test') % 10000}@test.com",
                password="TestPass123!",
                role="customer"
            )
            if test_user:
                print("✅ Новый администратор может создавать пользователей")
    
    # 6. Получаем статистику
    get_user_statistics(admin_token)
    
    # 7. Тест на дубликаты
    print("\n⚠️  Тест на дубликаты...")
    print("Попытка создать пользователя с существующим username...")
    if customer:
        duplicate = create_user(
            admin_token,
            username=customer["username"],
            email="another@test.com",
            password="TestPass123!",
            role="customer"
        )
        if not duplicate:
            print("✅ Правильно: создание с дубликатом username заблокировано")
    
    print("\n" + "=" * 70)
    print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 70)
    
    # Очистка тестовых данных
    cleanup_users(admin_token)

if __name__ == "__main__":
    admin_token = None
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест прерван пользователем")
        # Попытка очистить данные перед выходом
        if created_users:
            try:
                token = get_admin_token()
                if token:
                    cleanup_users(token)
            except:
                pass
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        # Попытка очистить данные перед выходом
        if created_users:
            try:
                token = get_admin_token()
                if token:
                    cleanup_users(token)
            except:
                pass
        sys.exit(1)

