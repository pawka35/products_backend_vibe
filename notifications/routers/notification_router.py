"""
Роутер для управления Telegram уведомлениями
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth.models import User as UserModel
from auth.utils import get_current_active_user
from notifications.schemas import (
    VerificationCodeRequest,
    VerificationCodeResponse,
    TelegramStatus,
    NotificationSettingsResponse,
    NotificationSettingsUpdate
)
from notifications.crud import (
    get_notification_settings,
    create_notification_settings,
    update_notification_settings,
    update_user_telegram_id,
    create_verification_code,
    verify_code
)
from notifications.services import TelegramService
from config import settings

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/telegram/request-code", response_model=VerificationCodeResponse)
async def request_verification_code(
    request: VerificationCodeRequest,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Запросить код верификации для привязки Telegram
    
    Пользователь должен:
    1. Получить код через этот endpoint
    2. Написать боту в Telegram: /verify <код>
    3. Бот автоматически привяжет Telegram ID к аккаунту
    """
    # Проверяем, не привязан ли уже Telegram
    if current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram уже привязан к вашему аккаунту. Используйте /notifications/telegram/disconnect для отвязки."
        )
    
    # Создаем код верификации
    verification_code = create_verification_code(db, current_user.id, expires_in_minutes=5)
    
    # Получаем имя бота из токена (первая часть до ':')
    bot_username = "your_bot"
    if settings.TELEGRAM_BOT_TOKEN and ':' in settings.TELEGRAM_BOT_TOKEN:
        # Пытаемся получить имя бота через API (опционально)
        try:
            telegram_service = TelegramService()
            bot_info = telegram_service._make_request("getMe", {})
            if bot_info:
                bot_username = bot_info.get("username", "your_bot")
        except:
            pass
    
    return VerificationCodeResponse(
        code=verification_code.code,
        expires_in=300,  # 5 минут в секундах
        message=f"Отправьте боту @{bot_username} команду: /verify {verification_code.code}"
    )


@router.get("/telegram/status", response_model=TelegramStatus)
async def get_telegram_status(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Получить статус подключения Telegram"""
    return TelegramStatus(
        connected=current_user.telegram_id is not None,
        telegram_id=current_user.telegram_id
    )


@router.delete("/telegram/disconnect")
async def disconnect_telegram(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Отвязать Telegram от аккаунта"""
    if not current_user.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram не привязан к вашему аккаунту"
        )
    
    update_user_telegram_id(db, current_user.id, None)
    
    return {"message": "Telegram успешно отвязан от аккаунта"}


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Получить настройки уведомлений"""
    settings_obj = get_notification_settings(db, current_user.id)
    
    if not settings_obj:
        # Создаем настройки по умолчанию, если их нет
        settings_obj = create_notification_settings(db, current_user.id)
    
    return NotificationSettingsResponse(
        telegram_enabled=settings_obj.telegram_enabled,
        notify_order_completed=settings_obj.notify_order_completed
    )


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings_endpoint(
    settings_update: NotificationSettingsUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить настройки уведомлений"""
    updated_settings = update_notification_settings(
        db,
        current_user.id,
        telegram_enabled=settings_update.telegram_enabled,
        notify_order_completed=settings_update.notify_order_completed
    )
    
    return NotificationSettingsResponse(
        telegram_enabled=updated_settings.telegram_enabled,
        notify_order_completed=updated_settings.notify_order_completed
    )


@router.post("/telegram/webhook")
async def telegram_webhook(
    update: dict,
    db: Session = Depends(get_db)
):
    """
    Webhook для обработки команд от Telegram бота
    
    Обрабатывает команды:
    - /verify <код> - верификация и привязка Telegram ID
    - /start - приветствие
    """
    from notifications.crud import get_user_by_telegram_id
    
    # Проверяем, что это сообщение
    if "message" not in update:
        return {"ok": True}
    
    message = update["message"]
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    if not chat_id or not text:
        return {"ok": True}
    
    # Обрабатываем команду /verify
    if text.startswith("/verify"):
        parts = text.split()
        if len(parts) != 2:
            # Неправильный формат команды
            telegram_service = TelegramService()
            telegram_service.send_message(
                chat_id,
                "❌ Неправильный формат команды.\n\nИспользование: /verify <код>\n\nПример: /verify 123456"
            )
            return {"ok": True}
        
        code = parts[1]
        
        try:
            # Проверяем код
            user = verify_code(db, code, chat_id)
            
            if user:
                # Успешная верификация
                telegram_service = TelegramService()
                telegram_service.send_message(
                    chat_id,
                    f"✅ <b>Telegram успешно привязан!</b>\n\n"
                    f"Ваш аккаунт: {user.username}\n"
                    f"Email: {user.email}\n\n"
                    f"Теперь вы будете получать уведомления о завершении заказов."
                )
            else:
                # Неверный или истекший код
                telegram_service = TelegramService()
                telegram_service.send_message(
                    chat_id,
                    "❌ Неверный или истекший код верификации.\n\n"
                    "Запросите новый код в веб-интерфейсе."
                )
        except ValueError as e:
            # Ошибка при верификации (например, Telegram ID уже привязан)
            telegram_service = TelegramService()
            telegram_service.send_message(
                chat_id,
                f"❌ Ошибка: {str(e)}"
            )
    
    # Обрабатываем команду /start
    elif text == "/start":
        # Проверяем, привязан ли уже этот Telegram ID
        user = get_user_by_telegram_id(db, chat_id)
        
        telegram_service = TelegramService()
        if user:
            telegram_service.send_message(
                chat_id,
                f"👋 <b>Привет, {user.username}!</b>\n\n"
                f"Ваш Telegram уже привязан к аккаунту.\n"
                f"Вы будете получать уведомления о завершении заказов."
            )
        else:
            telegram_service.send_message(
                chat_id,
                "👋 <b>Добро пожаловать!</b>\n\n"
                "Для привязки Telegram к вашему аккаунту:\n"
                "1. Запросите код верификации в веб-интерфейсе\n"
                "2. Отправьте боту команду: /verify <код>\n\n"
                "Пример: /verify 123456"
            )
    
    return {"ok": True}

