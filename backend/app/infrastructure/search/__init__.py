"""
Search Infrastructure - Meilisearch 全文搜索基础设施

提供 Meilisearch 索引管理和搜索能力封装。
"""

from app.infrastructure.search.meilisearch_client import (
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
