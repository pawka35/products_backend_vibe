# Application Package

# Импорт тестов для удобства
from .tests.test_admin import test_admin_functions
from .tests.test_api import test_api_flow

__all__ = ["test_admin_functions", "test_api_flow"]
