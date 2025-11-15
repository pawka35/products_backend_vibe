"""
Схемы Pydantic для API уведомлений
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class VerificationCodeRequest(BaseModel):
    """Запрос на получение кода верификации"""
    model_config = ConfigDict(from_attributes=True)


class VerificationCodeResponse(BaseModel):
    """Ответ с кодом верификации"""
    code: str = Field(..., description="6-значный код верификации")
    expires_in: int = Field(..., description="Время жизни кода в секундах")
    message: str = Field(..., description="Инструкция для пользователя")
    
    model_config = ConfigDict(from_attributes=True)


class TelegramStatus(BaseModel):
    """Статус подключения Telegram"""
    connected: bool = Field(..., description="Подключен ли Telegram")
    telegram_id: Optional[int] = Field(None, description="Telegram ID пользователя")
    
    model_config = ConfigDict(from_attributes=True)


class NotificationSettingsResponse(BaseModel):
    """Настройки уведомлений пользователя"""
    telegram_enabled: bool = Field(..., description="Включены ли Telegram уведомления")
    notify_order_completed: bool = Field(..., description="Уведомления о завершении заказа")
    
    model_config = ConfigDict(from_attributes=True)


class NotificationSettingsUpdate(BaseModel):
    """Обновление настроек уведомлений"""
    telegram_enabled: Optional[bool] = Field(None, description="Включить/выключить Telegram уведомления")
    notify_order_completed: Optional[bool] = Field(None, description="Включить/выключить уведомления о завершении заказа")
    
    model_config = ConfigDict(from_attributes=True)

