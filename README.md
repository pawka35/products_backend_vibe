# 🚀 FastAPI Backend with Docker & Nginx

Современное backend-приложение на FastAPI с контейнеризацией Docker и nginx прокси-сервером.

## ✨ Основные возможности

- **🔐 JWT аутентификация** - безопасная система входа пользователей
- **🔍 Поиск товаров** - интеграция с внешним API Maxi Retail
- **📄 Пагинация** - эффективная навигация по результатам поиска
- **🐳 Docker контейнеры** - легкое развертывание и масштабирование
- **🌐 Nginx прокси** - высокопроизводительный веб-сервер
- **🗄️ MySQL база данных** - надежное хранение данных
- **🧪 Тестирование** - полный набор unit и integration тестов

## 🏗️ Архитектура

```
backend/
├── app/           # Административные функции
├── auth/          # Аутентификация и авторизация
├── products/      # Управление товарами и поиск
├── nginx/         # Конфигурация nginx
├── Dockerfile     # Образ FastAPI приложения
└── docker-compose.yml  # Оркестрация контейнеров
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git

### Запуск проекта

1. **Клонировать репозиторий**
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

2. **Запустить контейнеры**
```bash
docker-compose up -d
```

3. **Проверить статус**
```bash
docker-compose ps
```

4. **Открыть в браузере**
- **API документация**: http://localhost/docs
- **Основное приложение**: http://localhost/
- **Health check**: http://localhost/health

## 🔧 API Endpoints

### Аутентификация
- `POST /auth/register` - Регистрация пользователя
- `POST /auth/token` - Получение JWT токена

### Поиск товаров
- `POST /search/products` - Поиск с пагинацией

### Административные функции
- `GET /admin/users` - Список пользователей
- `POST /admin/users` - Создание пользователя

### 🆕 Управление ролями (только для администраторов)
- `POST /admin/roles/` - Создание новой роли
- `GET /admin/roles/` - Список всех ролей с количеством пользователей
- `GET /admin/roles/{role_id}` - Получение роли по ID
- `PUT /admin/roles/{role_id}` - Обновление роли
- `DELETE /admin/roles/{role_id}` - Удаление роли
- `POST /admin/roles/{role_id}/activate` - Активация роли
- `POST /admin/roles/users/assign` - Назначение роли пользователю
- `GET /admin/roles/users/{user_id}` - Роли пользователя
- `GET /admin/roles/users/{user_id}/detailed` - Детальная информация о ролях пользователя
- `PUT /admin/roles/users/{user_role_id}` - Обновление роли пользователя
- `DELETE /admin/roles/users/{user_role_id}` - Удаление роли у пользователя
- `GET /admin/roles/{role_id}/users` - Пользователи с определенной ролью

## 🐳 Docker контейнеры

- **fastapi_app** - Основное приложение (порт 8000)
- **fastapi_mysql** - База данных MySQL (порт 3307)
- **fastapi_nginx** - Nginx прокси-сервер (порт 80)

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m pytest

# Запуск тестов поиска
python -m pytest products/tests/test_search.py -v

# Запуск тестов аутентификации
python -m pytest auth/tests/test_auth.py -v
```

## 📊 Мониторинг

- **Логи приложения**: `docker-compose logs fastapi`
- **Логи nginx**: `docker-compose logs nginx`
- **Логи MySQL**: `docker-compose logs mysql`

## 🔒 Безопасность

- JWT токены с настраиваемым временем жизни
- Хеширование паролей с bcrypt
- Валидация входных данных с Pydantic
- Защита от SQL-инъекций с SQLAlchemy

## 🚀 Развертывание

### Продакшн
1. Обновить переменные окружения в `docker-compose.yml`
2. Настроить SSL сертификаты для nginx
3. Настроить бэкапы MySQL
4. Мониторинг и логирование

### Разработка
1. Клонировать репозиторий
2. Установить зависимости: `pip install -r requirements.txt`
3. Настроить локальную базу данных
4. Запустить: `python main.py`

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создать feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Открыть Pull Request

## 📞 Поддержка

- Создать Issue в GitHub
- Обратиться к документации API: http://localhost/docs
