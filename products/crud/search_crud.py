from sqlalchemy.orm import Session
from products.models import SearchHistory
from datetime import datetime
from typing import List, Optional

def create_search_record(db: Session, user_id: int, query: str, results_count: int):
    """Создание записи о поиске"""
    search_record = SearchHistory(
        user_id=user_id,
        query=query,
        results_count=results_count
    )
    db.add(search_record)
    db.commit()
    db.refresh(search_record)
    return search_record

def get_user_search_history(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Получение истории поиска пользователя"""
    return db.query(SearchHistory).filter(
        SearchHistory.user_id == user_id
    ).order_by(
        SearchHistory.search_timestamp.desc()
    ).offset(skip).limit(limit).all()

def get_search_statistics(db: Session, user_id: Optional[int] = None):
    """Получение статистики поиска"""
    query = db.query(SearchHistory)
    
    if user_id:
        query = query.filter(SearchHistory.user_id == user_id)
    
    total_searches = query.count()
    
    # Популярные запросы
    popular_queries = db.query(
        SearchHistory.query,
        db.func.count(SearchHistory.id).label('count')
    ).group_by(SearchHistory.query).order_by(
        db.func.count(SearchHistory.id).desc()
    ).limit(10).all()
    
    return {
        "total_searches": total_searches,
        "popular_queries": [{"query": q.query, "count": q.count} for q in popular_queries]
    }

def delete_search_record(db: Session, search_id: int, user_id: int):
    """Удаление записи о поиске (только свои записи)"""
    search_record = db.query(SearchHistory).filter(
        SearchHistory.id == search_id,
        SearchHistory.user_id == user_id
    ).first()
    
    if not search_record:
        return False
    
    db.delete(search_record)
    db.commit()
    return True

def clear_user_search_history(db: Session, user_id: int):
    """Очистка всей истории поиска пользователя"""
    deleted_count = db.query(SearchHistory).filter(
        SearchHistory.user_id == user_id
    ).delete()
    
    db.commit()
    return deleted_count
