# Products Application

Модуль для управления заказами и продуктами в системе FastAPI.

## Структура

```
products/
├── __init__.py
├── models/           # Модели данных
│   ├── __init__.py
│   ├── product_models.py
│   └── search_models.py
├── schemas/          # Pydantic схемы
│   ├── __init__.py
│   ├── product_schemas.py
│   └── search_schemas.py
├── crud/            # CRUD операции
│   ├── __init__.py
│   ├── product_crud.py
│   └── search_crud.py
├── routers/         # FastAPI роутеры
│   ├── __init__.py
│   ├── orders.py    # Роутер для заказчиков
│   ├── executor.py  # Роутер для исполнителей
│   └── search.py    # Роутер для поиска товаров
├── services/        # Бизнес-логика
│   ├── __init__.py
│   └── search_service.py
├── tests/           # Тесты
│   ├── test_orders.py
│   └── test_search.py
└── README.md
```

## Функционал

### 🔵 Customer (Заказчик)
- Создание заказов с продуктами
- Просмотр своих заказов
- Отмена заказов
- Просмотр сводки по заказам

### 🟡 Executor (Исполнитель)
- Просмотр доступных заказов
- Начало исполнения заказа
- Отметка продуктов как купленных
- Завершение заказов
- Фильтрация по статусам

### 🔍 Search (Поиск товаров)
- Поиск товаров на внешних сайтах (Maxi Retail)
- Пагинация результатов поиска
- Настройка количества элементов на странице
- Информация о количестве страниц и элементов

## Модели данных

### Order (Заказ)
- `id` - уникальный идентификатор
- `customer_id` - ID заказчика
- `status` - статус заказа (pending, in_progress, completed, cancelled)
- `created_at` - время создания
- `updated_at` - время обновления
- `completed_at` - время завершения

### Product (Продукт)
- `id` - уникальный идентификатор
- `name` - название продукта
- `quantity` - количество
- `notes` - примечания
- `is_purchased` - куплен ли продукт
- `purchased_at` - время покупки
- `purchased_by` - ID исполнителя
- `order_id` - ID заказа

### ExternalProduct (Внешний товар)
- `id` - ID товара на внешнем сайте
- `name` - название товара
- `price` - цена
- `image` - URL изображения
- `url` - URL товара
- `description` - описание
- `search_query` - поисковый запрос
- `source` - источник (сайт)

## API Endpoints

### Заказы (Customer)
- `POST /orders/` - создание заказа
- `GET /orders/` - список заказов пользователя
- `GET /orders/{order_id}` - детали заказа
- `GET /orders/{order_id}/summary` - сводка по заказу
- `PUT /orders/{order_id}/cancel` - отмена заказа

### Исполнители (Executor)
- `GET /executor/orders` - доступные заказы
- `GET /executor/orders/{order_id}` - детали заказа
- `GET /executor/orders/{order_id}/summary` - сводка по заказу
- `PUT /executor/orders/{order_id}/start` - начало исполнения
- `PUT /executor/products/{product_id}/purchase` - отметка покупки
- `PUT /executor/orders/{order_id}/complete` - завершение заказа
- `GET /executor/orders/status/{status}` - заказы по статусу

### Поиск товаров
- `POST /search/products` - поиск товаров с пагинацией

## Поиск товаров

### Параметры запроса
- `query` (обязательный) - поисковый запрос
- `page` (опционально) - номер страницы (по умолчанию 1)

### Ответ
```json
{
  "query": "молоко",
  "total_found": 45,
  "total_pages": 3,
  "current_page": 1,
  "products": [...],
  "search_timestamp": "2024-01-01T12:00:00",
  "source": "maxi-retail.ru"
}
```

### Пагинация
- Количество страниц рассчитывается как `total_found / per_page` (округление вверх)
- Номер страницы начинается с 1
- При некорректном номере страницы автоматически устанавливается ближайшее валидное значение

## Использование

```python
# Импорт роутеров
from products.routers import orders_router, executor_router, search_router

# Подключение к FastAPI приложению
app.include_router(orders_router)
app.include_router(executor_router)
app.include_router(search_router)
```

## Тестирование

```bash
# Запуск теста функционала заказов
python products/tests/test_orders.py

# Запуск тестов поиска
python -m pytest products/tests/test_search.py

# Или через общий скрипт
python run_tests.py orders
python run_tests.py search
```

## Зависимости

- FastAPI
- SQLAlchemy
- Pydantic
- aiohttp (для внешних запросов)
- BeautifulSoup4 (для парсинга HTML)
- Python 3.8+
