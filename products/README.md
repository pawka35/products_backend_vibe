# 📦 Модуль продуктов и заказов

Полнофункциональная система управления заказами, продуктами и поиска товаров для FastAPI приложения.

## 🚀 Основные возможности

### 📋 Система заказов
- **Создание заказов** с множественными продуктами
- **Исполнение заказов** через систему исполнителей
- **Отслеживание статуса** заказов
- **Управление продуктами** в заказах

### 🔍 Поиск продуктов
- **Интеграция с внешним API** (MaxiRetail)
- **Пагинация результатов** поиска
- **Кэширование результатов** для оптимизации
- **Гибкие параметры** поиска

### 👥 Роли в системе
- **Customer** - создание и управление заказами
- **Executor** - исполнение заказов
- **Admin** - полный доступ к системе

## 🏗️ Архитектура

```
products/
├── crud/                    # CRUD операции
│   ├── product_crud.py      # Операции с продуктами
│   └── search_crud.py       # Операции поиска
├── models/                  # SQLAlchemy модели
│   ├── product_models.py    # Модели продуктов
│   └── search_models.py     # Модели поиска
├── routers/                 # API роутеры
│   ├── orders.py            # Управление заказами
│   ├── executor.py          # Исполнение заказов
│   └── search.py            # Поиск продуктов
├── schemas/                 # Pydantic схемы
│   ├── product_schemas.py   # Схемы продуктов
│   └── search_schemas.py    # Схемы поиска
├── services/                # Бизнес-логика
│   └── search_service.py    # Сервис поиска
├── tests/                   # Тесты
│   ├── test_orders.py       # Тесты заказов
│   └── test_search.py       # Тесты поиска
└── README.md                # Документация
```

## 📚 API Endpoints

### Заказы
- `GET /orders/` - Список всех заказов
- `POST /orders/` - Создание нового заказа
- `GET /orders/{id}/summary` - Сводка по заказу

### Исполнение заказов
- `GET /executor/orders` - Доступные заказы для исполнения
- `PUT /executor/orders/{id}/start` - Начало исполнения заказа
- `PUT /executor/products/{id}/purchase` - Отметка продукта как купленного
- `PUT /executor/orders/{id}/complete` - Завершение заказа

### Поиск продуктов
- `POST /products/search` - Поиск продуктов с пагинацией

## 🔒 Модели данных

### Order (Заказ)
```python
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = Column(DECIMAL(10, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### OrderProduct (Продукт в заказе)
```python
class OrderProduct(Base):
    __tablename__ = "order_products"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price = Column(DECIMAL(10, 2), nullable=False)
    is_purchased = Column(Boolean, default=False)
    purchased_at = Column(DateTime(timezone=True), nullable=True)
```

### OrderStatus (Статус заказа)
```python
class OrderStatus(str, enum.Enum):
    PENDING = "pending"           # Ожидает исполнения
    IN_PROGRESS = "in_progress"   # В процессе исполнения
    COMPLETED = "completed"       # Завершен
    CANCELLED = "cancelled"       # Отменен
```

## 🔍 Система поиска

### MaxiRetailSearchService
```python
class MaxiRetailSearchService:
    def search_products(self, query: str, page: int = 1) -> ProductSearchResponse:
        """
        Поиск продуктов с пагинацией
        
        Args:
            query: Поисковый запрос
            page: Номер страницы (начиная с 1)
        
        Returns:
            ProductSearchResponse с результатами и пагинацией
        """
```

### Пагинация
- **Страницы начинаются с 1**
- **Размер страницы**: 20 продуктов
- **Автоматический расчет** общего количества страниц
- **Защита от деления на ноль**

### Структура ответа поиска
```python
class ProductSearchResponse(BaseModel):
    products: List[ExternalProduct]
    pagination: PaginationInfo
    total_count: int
    current_page: int
    total_pages: int
```

## 📋 Жизненный цикл заказа

### 1. Создание заказа
```python
# POST /orders/
{
    "products": [
        {"name": "Хлеб", "quantity": 2, "price": 50.00},
        {"name": "Молоко", "quantity": 1, "price": 80.00}
    ]
}
```

### 2. Исполнение заказа
1. **Executor** получает список доступных заказов
2. **Начинает исполнение** конкретного заказа
3. **Отмечает продукты** как купленные
4. **Завершает заказ** когда все продукты куплены

### 3. Статусы заказа
- `pending` → `in_progress` → `completed`
- Возможен переход в `cancelled` на любом этапе

## 🧪 Тестирование

### Запуск тестов
```bash
# Тесты заказов
python products/tests/test_orders.py

# Тесты поиска
cd products && python -m pytest tests/test_search.py -v

# Все тесты модуля
python -m pytest products/tests/ -v
```

### Покрытие тестами
- ✅ Создание и управление заказами
- ✅ Исполнение заказов
- ✅ Поиск продуктов
- ✅ Пагинация
- ✅ Валидация данных

## 📊 Примеры использования

### Создание заказа
```python
# POST /orders/
{
    "products": [
        {"name": "Яблоки", "quantity": 5, "price": 120.00},
        {"name": "Бананы", "quantity": 3, "price": 90.00}
    ]
}

# Ответ
{
    "id": 1,
    "customer_id": 1,
    "status": "pending",
    "total_amount": 870.00,
    "products": [...]
}
```

### Поиск продуктов
```python
# POST /products/search
{
    "query": "хлеб",
    "page": 1
}

# Ответ
{
    "products": [...],
    "pagination": {
        "current_page": 1,
        "total_pages": 3,
        "has_next": true,
        "has_prev": false
    },
    "total_count": 45,
    "current_page": 1,
    "total_pages": 3
}
```

### Исполнение заказа
```python
# 1. Начало исполнения
PUT /executor/orders/1/start

# 2. Отметка покупки продукта
PUT /executor/products/1/purchase

# 3. Завершение заказа
PUT /executor/orders/1/complete
```

## 🔧 Настройка

### Переменные окружения
```bash
# Настройки поиска
SEARCH_API_URL=https://api.maxi-retail.com
SEARCH_API_KEY=your-api-key
SEARCH_CACHE_TTL=3600

# Настройки пагинации
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

### Внешние API
- **MaxiRetail** - основной источник данных о продуктах
- **Кэширование** результатов для оптимизации
- **Обработка ошибок** внешних API

## 📝 Логирование

- **Создание заказов** - логируется customer_id и продукты
- **Исполнение заказов** - логируется executor_id и действия
- **Поиск продуктов** - логируется запрос и результаты
- **Ошибки** - детальное логирование для отладки

## 🚨 Ограничения

### Заказы
- **Только customer** может создавать заказы
- **Только executor** может исполнять заказы
- **Нельзя изменить** заказ после начала исполнения

### Поиск
- **Максимум 100 продуктов** на страницу
- **Кэш истекает** через 1 час
- **Ограничения** внешнего API

## 🔄 Миграции

### Добавление новых полей
1. Обновить модель в `models/`
2. Обновить схему в `schemas/`
3. Обновить CRUD операции
4. Запустить миграцию базы данных

### Добавление новых статусов
1. Добавить в enum `OrderStatus`
2. Обновить логику переходов
3. Обновить тесты

## 📈 Мониторинг

### Метрики
- Количество созданных заказов
- Время исполнения заказов
- Популярность поисковых запросов
- Ошибки внешних API

### Health checks
- Доступность внешнего API
- Состояние базы данных
- Время ответа поиска

## 🔒 Безопасность

### Авторизация
- **Customer** - доступ только к своим заказам
- **Executor** - доступ только к доступным заказам
- **Admin** - полный доступ ко всем данным

### Валидация
- Проверка количества продуктов
- Валидация цен
- Проверка статусов заказов

---

**Модуль готов к использованию в продакшене! 🚀**
