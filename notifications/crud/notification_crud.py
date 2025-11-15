"""
CRUD операции для управления уведомлениями
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string

from notifications.models import NotificationSettings, TelegramVerificationCode
from auth.models import User


def get_notification_settings(db: Session, user_id: int) -> Optional[NotificationSettings]:
    """Получить настройки уведомлений пользователя"""
    return db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()


def create_notification_settings(db: Session, user_id: int) -> NotificationSettings:
    """Создать настройки уведомлений для пользователя (по умолчанию все включено)"""
    settings = NotificationSettings(
        user_id=user_id,
        telegram_enabled=True,
        notify_order_completed=True
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_notification_settings(
    db: Session, 
    user_id: int, 
    telegram_enabled: Optional[bool] = None,
    notify_order_completed: Optional[bool] = None
) -> NotificationSettings:
    """Обновить настройки уведомлений пользователя"""
    settings = get_notification_settings(db, user_id)
    
    if not settings:
        settings = create_notification_settings(db, user_id)
    
    if telegram_enabled is not None:
        settings.telegram_enabled = telegram_enabled
    if notify_order_completed is not None:
        settings.notify_order_completed = notify_order_completed
    
    db.commit()
    db.refresh(settings)
    return settings


def update_user_telegram_id(db: Session, user_id: int, telegram_id: Optional[int]) -> User:
    """Обновить Telegram ID пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"Пользователь с ID {user_id} не найден")
    
    # Проверяем уникальность telegram_id (если он не None)
    if telegram_id is not None:
        existing_user = db.query(User).filter(
            and_(User.telegram_id == telegram_id, User.id != user_id)
        ).first()
        if existing_user:
            raise ValueError(f"Telegram ID {telegram_id} уже привязан к другому пользователю")
    
    user.telegram_id = telegram_id
    db.commit()
    db.refresh(user)
    return user


def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
    """Получить пользователя по Telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def generate_verification_code(length: int = 6) -> str:
    """Генерирует случайный код верификации"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def create_verification_code(
    db: Session, 
    user_id: int, 
    expires_in_minutes: int = 5
) -> TelegramVerificationCode:
    """
    Создает код верификации для пользователя
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        expires_in_minutes: Время жизни кода в минутах (по умолчанию 5)
    
    Returns:
        Объект TelegramVerificationCode
    """
    # Удаляем старые неиспользованные коды для этого пользователя
    db.query(TelegramVerificationCode).filter(
        and_(
            TelegramVerificationCode.user_id == user_id,
            TelegramVerificationCode.used == False,
            TelegramVerificationCode.expires_at > datetime.utcnow()
        )
    ).delete()
    
    # Генерируем новый код
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
    
    verification_code = TelegramVerificationCode(
        user_id=user_id,
        code=code,
        expires_at=expires_at,
        used=False
    )
    
    db.add(verification_code)
    db.commit()
    db.refresh(verification_code)
    
    return verification_code


def verify_code(
    db: Session, 
    code: str, 
    telegram_id: int
) -> Optional[User]:
    """
    Проверяет код верификации и привязывает Telegram ID к пользователю
    
    Args:
        db: Сессия базы данных
        code: Код верификации
        telegram_id: Telegram ID пользователя
    
    Returns:
        Объект User, если код верный, None в противном случае
    """
    # Ищем неиспользованный код, который еще не истек
    verification_code = db.query(TelegramVerificationCode).filter(
        and_(
            TelegramVerificationCode.code == code,
            TelegramVerificationCode.used == False,
            TelegramVerificationCode.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not verification_code:
        return None
    
    # Проверяем, не привязан ли уже этот Telegram ID к другому пользователю
    existing_user = get_user_by_telegram_id(db, telegram_id)
    if existing_user and existing_user.id != verification_code.user_id:
        # Помечаем код как использованный, чтобы его нельзя было использовать повторно
        verification_code.used = True
        db.commit()
        raise ValueError(f"Telegram ID {telegram_id} уже привязан к другому пользователю")
    
    # Получаем пользователя
    user = db.query(User).filter(User.id == verification_code.user_id).first()
    if not user:
        verification_code.used = True
        db.commit()
        return None
    
    # Привязываем Telegram ID
    user.telegram_id = telegram_id
    verification_code.telegram_id = telegram_id
    verification_code.used = True
    
    # Создаем настройки уведомлений, если их нет
    from notifications.crud import get_notification_settings, create_notification_settings
    if not get_notification_settings(db, user.id):
        create_notification_settings(db, user.id)
    
    db.commit()
    db.refresh(user)
    
    return user


def cleanup_expired_codes(db: Session, older_than_hours: int = 24):
    """
    Удаляет истекшие коды верификации (для периодической очистки)
    
    Args:
        db: Сессия базы данных
        older_than_hours: Удалять коды старше указанного количества часов
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
    
    deleted_count = db.query(TelegramVerificationCode).filter(
        TelegramVerificationCode.expires_at < cutoff_time
    ).delete()
    
    db.commit()
    return deleted_count

