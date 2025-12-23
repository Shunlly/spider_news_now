"""
存储模块初始化（向后兼容层）

注意：此模块已迁移至 app.infrastructure.storage
请在新代码中使用 from app.infrastructure.storage import ...
"""

# 向后兼容导出
from app.infrastructure.storage import (
    BaseStorageProvider,
    LocalStorage,
    MinioStorage,
    S3Storage,
    StorageProvider,
    clear_storage_cache,
    get_storage_provider,
)

__all__ = [
    "StorageProvider",
    "BaseStorageProvider",
    "MinioStorage",
    "S3Storage",
    "LocalStorage",
    "get_storage_provider",
    "clear_storage_cache",
]
