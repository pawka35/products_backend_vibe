import pytest
from unittest.mock import AsyncMock, patch
from products.services.search_service import MaxiRetailSearchService
from products.schemas.search_schemas import ProductSearchRequest, ProductSearchResponse
from products.routers.search import router
from datetime import datetime

class TestSearchService:
    """Тесты для сервиса поиска"""
    
    @pytest.fixture
    def search_service(self):
        """Фикстура для создания сервиса поиска"""
        service = MaxiRetailSearchService()
        return service
    
    def test_pagination_calculation(self, search_service):
        """Тест расчета пагинации"""
        # Тест с пустым списком
        pagination = search_service._create_pagination_info(24, 0, 1)
        assert pagination["total_pages"] == 0
        assert pagination["has_next"] == False
        assert pagination["has_prev"] == False
        
        # Тест с одной страницей
        pagination = search_service._create_pagination_info(24, 20, 1)
        assert pagination["total_pages"] == 1
        assert pagination["has_next"] == False
        assert pagination["has_prev"] == False
        
        # Тест с несколькими страницами
        pagination = search_service._create_pagination_info(24, 50, 2)
        assert pagination["total_pages"] == 3
        assert pagination["has_next"] == True
        assert pagination["has_prev"] == True
    
    def test_pagination_edge_cases(self, search_service):
        """Тест граничных случаев пагинации"""
        # Тест с одной страницей
        pagination = search_service._create_pagination_info(24, 20, 1)
        assert pagination["current_page"] == 1
        assert pagination["total_pages"] == 1
        
        # Тест с несколькими страницами
        pagination = search_service._create_pagination_info(24, 100, 3)
        assert pagination["current_page"] == 3
        assert pagination["total_pages"] == 5

class TestSearchSchemas:
    """Тесты для схем поиска"""
    
    def test_product_search_request_defaults(self):
        """Тест значений по умолчанию для запроса поиска"""
        request = ProductSearchRequest(query="тест")
        assert request.page == 1
    
    def test_product_search_response_structure(self):
        """Тест структуры ответа поиска"""
        response = ProductSearchResponse(
            query="тест",
            total_found=10,
            total_pages=2,
            current_page=1,
            has_next=True,
            has_prev=False,
            products=[],
            search_timestamp=datetime.now(),
            source="maxi-retail.ru"
        )
        
        assert response.query == "тест"
        assert response.total_found == 10
        assert response.total_pages == 2
        assert response.current_page == 1
        assert response.has_next == True
        assert response.has_prev == False

class TestSearchRouter:
    """Тесты для роутера поиска"""
    
    def test_router_import(self):
        """Тест импорта роутера"""
        assert router is not None
        assert hasattr(router, 'routes')
    
    def test_search_endpoint_exists(self):
        """Тест существования эндпоинта поиска"""
        # Проверяем, что роутер имеет маршруты
        assert len(router.routes) > 0
        
        # Проверяем, что есть хотя бы один POST маршрут
        post_routes = [route for route in router.routes if hasattr(route, 'methods') and 'POST' in route.methods]
        assert len(post_routes) > 0
