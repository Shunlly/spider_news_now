"""
Meilisearch 全文搜索服务（向后兼容层）

注意：此模块已迁移至 app.infrastructure.search
请在新代码中使用 from app.infrastructure.search import ...
"""

# 向后兼容导出
from app.infrastructure.search import (
    FacetDistribution,
    SearchHit,
    SearchResult,
    SearchService,
    get_search_service,
)

__all__ = [
    "SearchService",
    "SearchHit",
    "SearchResult",
    "FacetDistribution",
    "get_search_service",
]
