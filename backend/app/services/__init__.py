# Services package
"""
服务层模块
Service Layer Module

提供业务逻辑服务，包括：
- 去重服务 (DuplicateService)
- 搜索服务 (SearchService)
- 导出服务 (ExportService)
- 存储服务 (StorageService)
- 新闻服务 (NewsService)
- 爬虫服务 (ScraperService)
"""

from app.services.storage_service import StorageService, get_storage_service
from app.services.dedup_service import DuplicateService, get_dedup_service
from app.services.export_service import DataSource, ExportService
from app.services.search_service import SearchService, get_search_service

__all__ = [
    "DuplicateService",
    "get_dedup_service",
    "SearchService",
    "get_search_service",
    "ExportService",
    "DataSource",
    "StorageService",
    "get_storage_service",
]
