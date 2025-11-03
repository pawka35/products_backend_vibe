"""
Скрипт инициализации базовых ролей в системе.
Запускается автоматически при старте приложения.
"""
from sqlalchemy.orm import Session
from auth.models.role_models import Role
from auth.crud.role_crud import role_assignment_crud


def ensure_basic_roles(db: Session) -> dict:
    """
    Убедиться, что базовые роли существуют в таблице roles.
    Создает роли admin, customer, executor если их нет.
    
    Args:
        db: Сессия базы данных
        
    Returns:
        dict со статусом создания ролей
    """
    basic_roles = [
        {
            "name": "admin",
            "description": "Администратор системы - полный доступ ко всем функциям",
            "permissions": None,
            "is_active": True
        },
        {
            "name": "customer", 
            "description": "Заказчик - может создавать заказы, искать товары, управлять своими заказами",
            "permissions": None,
            "is_active": True
        },
        {
            "name": "executor",
            "description": "Исполнитель - может принимать заказы, покупать товары, обновлять статус покупок",
            "permissions": None,
            "is_active": True
        }
    ]
    
    created_roles = []
    existing_roles = []
    
    for role_data in basic_roles:
        # Проверяем, существует ли роль
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        
        if existing_role:
            existing_roles.append(role_data["name"])
        else:
            # Создаем новую роль
            db_role = Role(**role_data)
            db.add(db_role)
            created_roles.append(role_data["name"])
    
    if created_roles:
        db.commit()
        print(f"✅ Созданы базовые роли: {', '.join(created_roles)}")
    
    if existing_roles:
        print(f"ℹ️  Роли уже существуют: {', '.join(existing_roles)}")
    
    return {
        "created": created_roles,
        "existing": existing_roles,
        "total": len(basic_roles)
    }


def migrate_user_roles_to_assignments(db: Session, force: bool = False) -> dict:
    """
    Опциональная миграция: создает записи в user_roles на основе поля role в таблице users.
    Это не обязательно, так как User.get_roles() уже учитывает базовую роль,
    но может быть полезно для полной миграции на систему множественных ролей.
    
    Args:
        db: Сессия базы данных
        force: Если True, создает записи даже если они уже существуют
        
    Returns:
        dict со статистикой миграции
    """
    from auth.models.user_models import User
    from auth.models.role_models import Role, RoleAssignment
    from datetime import datetime
    
    # Получаем все роли
    roles_map = {}
    for role in db.query(Role).all():
        roles_map[role.name] = role.id
    
    # Получаем всех пользователей
    users = db.query(User).all()
    
    migrated = 0
    skipped = 0
    errors = []
    
    for user in users:
        role_name = user.role.value
        
        if role_name not in roles_map:
            errors.append(f"Роль '{role_name}' не найдена для пользователя {user.username}")
            continue
        
        role_id = roles_map[role_name]
        
        # Проверяем, есть ли уже запись
        existing = db.query(RoleAssignment).filter(
            RoleAssignment.user_id == user.id,
            RoleAssignment.role_id == role_id
        ).first()
        
        if existing and not force:
            skipped += 1
            continue
        
        if not existing:
            # Создаем новую запись
            role_assignment = RoleAssignment(
                user_id=user.id,
                role_id=role_id,
                assigned_by=None,  # Системное назначение
                assigned_at=datetime.now(),
                expires_at=None,
                is_active=True
            )
            db.add(role_assignment)
            migrated += 1
    
    if migrated > 0:
        db.commit()
        print(f"✅ Мигрировано ролей: {migrated}")
    
    if skipped > 0:
        print(f"ℹ️  Пропущено (уже существуют): {skipped}")
    
    if errors:
        print(f"⚠️  Ошибки: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
    
    return {
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors,
        "total_users": len(users)
    }


if __name__ == "__main__":
    """
    Запуск скрипта напрямую для тестирования
    """
    from database import SessionLocal
    
    print("=" * 70)
    print("🔧 ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ МНОЖЕСТВЕННЫХ РОЛЕЙ")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Шаг 1: Создаем базовые роли
        print("\n📝 Шаг 1: Создание базовых ролей...")
        roles_result = ensure_basic_roles(db)
        
        # Шаг 2: Опциональная миграция (закомментировано по умолчанию)
        # print("\n📝 Шаг 2: Миграция существующих ролей пользователей...")
        # migration_result = migrate_user_roles_to_assignments(db, force=False)
        
        print("\n" + "=" * 70)
        print("✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
        print("=" * 70)
        print(f"\nРезультаты:")
        print(f"  - Создано ролей: {len(roles_result['created'])}")
        print(f"  - Уже существовало: {len(roles_result['existing'])}")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

