from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"      # Ожидает исполнения
    IN_PROGRESS = "in_progress"  # В процессе исполнения
    COMPLETED = "completed"   # Исполнен
    CANCELLED = "cancelled"   # Отменен

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    notes = Column(Text, nullable=True)
    is_purchased = Column(Boolean, default=False)
    purchased_at = Column(DateTime(timezone=True), nullable=True)
    purchased_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Связи
    order = relationship("Order", back_populates="products")
    purchaser = relationship("User", foreign_keys=[purchased_by])

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Связи
    customer = relationship("User", back_populates="orders")
    products = relationship("Product", back_populates="order", cascade="all, delete-orphan")
