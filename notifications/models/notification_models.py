from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class NotificationSettings(Base):
    """Модель настроек уведомлений пользователя"""
    __tablename__ = "notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    telegram_enabled = Column(Boolean, default=True)
    notify_order_completed = Column(Boolean, default=True)  # Уведомления о завершении заказа
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    user = relationship("User", back_populates="notification_settings")
    
    def __repr__(self):
        return f"<NotificationSettings(user_id={self.user_id}, telegram_enabled={self.telegram_enabled})>"


class TelegramVerificationCode(Base):
    """Модель для временных кодов верификации Telegram"""
    __tablename__ = "telegram_verification_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(6), nullable=False, index=True)  # 6-значный код
    telegram_id = Column(Integer, nullable=True)  # Telegram ID пользователя (заполняется при верификации)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<TelegramVerificationCode(user_id={self.user_id}, code={self.code}, used={self.used})>"

