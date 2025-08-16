import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import json
import re
from fastapi import HTTPException
import math

class MaxiRetailSearchService:
    """Сервис для поиска товаров на Maxi Retail"""
    
    BASE_URL = "https://maxi-retail.ru/vologda/search"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    async def search_products(self, query: str, page: int = 1) -> Tuple[List[Dict], Dict]:
        """
        Поиск товаров по запросу с пагинацией
        
        Args:
            query: Поисковый запрос
            page: Номер страницы (начиная с 1)
            
        Returns:
            Кортеж (список товаров, информация о пагинации)
        """
        if not query.strip():
            return [], self._create_pagination_info(0, page, 24)
        
        try:
            # Формируем URL для поиска
            search_url = f"{self.BASE_URL}?q={query}"
            
            # Делаем запрос к сайту
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Ошибка при поиске товаров: HTTP {response.status}"
                    )
                
                html_content = await response.text()
                
                # Парсим HTML
                all_products, count = await self._parse_search_results(html_content, query)
                
                # Применяем пагинацию
                pagination_info = self._create_pagination_info(len(all_products), count, page)
                
                return all_products, pagination_info
                
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Ошибка сети при поиске товаров: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Неожиданная ошибка при поиске товаров: {str(e)}"
            )
    
    
    def _create_pagination_info(self, per_page: int, total_items: int, current_page: int) -> Dict:
        """
        Создает информацию о пагинации
        
        Args:
            total_items: Общее количество элементов
            current_page: Текущая страница
            per_page: Количество элементов на странице
            
        Returns:
            Словарь с информацией о пагинации
        """
        total_pages = math.ceil(total_items /per_page) if total_items > 0 else 0
        
        return {
            "current_page": current_page,
            "total_pages": total_pages,
            "total_items": total_items,
            "has_next": current_page < total_pages,
            "has_prev": current_page > 1
        }
    
    async def _parse_search_results(self, html_content: str, query: str) -> List[Dict]:
        """
        Парсинг результатов поиска из HTML
        
        Args:
            html_content: HTML содержимое страницы
            query: Исходный поисковый запрос
            
        Returns:
            Список товаров
        """
        products = []
        
        try:
            # Парсим HTML с помощью BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Ищем скрипт с данными о товарах
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string and 'ProductList' in script.string:
                    # Извлекаем данные о товарах
                    products, count = self._extract_products_from_script(script.string)
           
            # Фильтруем и форматируем результаты
            formatted_products = []
            for product in products:
                if self._is_valid_product(product):
                    formatted_product = self._format_product(product, query)
                    formatted_products.append(formatted_product)
            
            return formatted_products, count
            
        except Exception as e:
            # Логируем ошибку, но возвращаем пустой список
            print(f"Ошибка при парсинге результатов поиска: {e}")
            return []
    
    def _extract_products_from_script(self, script_content: str) -> List[Dict]:
        """
        Извлечение данных о товарах из JavaScript кода
        
        Args:
            script_content: Содержимое скрипта
            
        Returns:
            Список товаров
        """
        products = []
        
        try:
            products_match = re.search(r'"products":\s*(\[[\s\S]*?\])', script_content)
            count_match = re.search(r'"count":\s*(\d+)', script_content)

            if products_match and count_match:
                products_json = products_match.group(1)
                count = int(count_match.group(1))
                products = json.loads(products_json)
                return products, count
                
        except (json.JSONDecodeError, Exception) as e:
            print(f"Ошибка при извлечении товаров из скрипта: {e}")
        
        return []
    
   
    def _is_valid_product(self, product: Dict) -> bool:
        """
        Проверка валидности товара
        
        Args:
            product: Словарь с данными о товаре
            
        Returns:
            True если товар валиден
        """
        # Проверяем наличие обязательных полей
        required_fields = ['name']
        
        for field in required_fields:
            if field not in product or not product[field]:
                return False
        
        return True
    
    def _format_product(self, product: Dict, query: str) -> Dict:
        """
        Форматирование товара для ответа API
        
        Args:
            product: Исходные данные о товаре
            query: Поисковый запрос
            
        Returns:
            Отформатированный товар
        """
        formatted = {
            'id': product.get('id', None),
            'name': product.get('name', ''),
            'price': product.get('price', None),
            'image': product.get('image', None),
            'url': product.get('url', None),
            'description': product.get('description', ''),
            'search_query': query,
            'source': 'maxi-retail.ru'
        }
        
        # Убираем None значения
        formatted = {k: v for k, v in formatted.items() if v is not None}
        
        return formatted

# Синхронная версия для совместимости
class MaxiRetailSearchServiceSync:
    """Синхронная версия сервиса поиска"""
    
    def __init__(self):
        self.search_service = MaxiRetailSearchService()
    
    def search_products(self, query: str, page: int = 1) -> Tuple[List[Dict], Dict]:
        """
        Синхронный поиск товаров с пагинацией
        
        Args:
            query: Поисковый запрос
            page: Номер страницы (начиная с 1)
            
        Returns:
            Кортеж (список товаров, информация о пагинации)
        """
        async def async_search():
            async with self.search_service as service:
                return await service.search_products(query, page)
        
        return asyncio.run(async_search())
