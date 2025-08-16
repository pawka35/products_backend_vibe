from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class SearchHistory(Base):
    """Модель истории поиска товаров"""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(String(255), nullable=False)
    results_count = Column(Integer, default=0)
    search_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    user = relationship("User", back_populates="search_history")

# Добавляем связь в модель User (auth/models/user_models.py)
# user_models.py уже содержит orders = relationship("Order", back_populates="customer")
# Добавим туда: search_history = relationship("SearchHistory", back_populates="user")
