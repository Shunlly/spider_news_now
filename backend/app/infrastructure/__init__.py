"""
Infrastructure Layer - 基础设施层

包含所有技术基础设施组件：
- database: 数据库连接和会话管理
- cache: Redis 缓存服务
- search: Meilisearch 全文搜索
- storage: 对象存储 (MinIO/S3/Local)
"""

# Database
# Cache
from app.infrastructure.cache import (
    RedisService,
    get_redis,
    get_redis_client,
)
from app.infrastructure.database import (
    AsyncSessionLocal,
    Base,
    async_session_maker,
    engine,
    get_async_session,
    get_db,
)

# Search
from app.infrastructure.search import (
    FacetDistribution,
    SearchHit,
    SearchResult,
    SearchService,
    get_search_service,
)

# Storage
from app.infrastructure.storage import (
    BaseStorageProvider,
    LocalStorage,
    MinioStorage,
    StorageProvider,
    get_storage_provider,
)

__all__ = [
    # Database
    "Base",
    "engine",
    "AsyncSessionLocal",
    "async_session_maker",
    "get_db",
    "get_async_session",
    # Cache
    "RedisService",
    "get_redis",
    "get_redis_client",
    # Search
    "SearchService",
    "SearchHit",
    "SearchResult",
    "FacetDistribution",
    "get_search_service",
    # Storage
    "StorageProvider",
    "BaseStorageProvider",
    "MinioStorage",
    "LocalStorage",
    "get_storage_provider",
]
