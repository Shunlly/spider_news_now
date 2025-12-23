"""
Storage Infrastructure - 对象存储基础设施

提供统一的存储接口，支持多种存储后端：
- MinIO / S3 兼容存储
- AWS S3（使用 boto3）
- 本地文件存储
- 阿里云 OSS（待实现）
"""

import logging
from functools import lru_cache

from app.core.config import settings
from app.infrastructure.storage.local import LocalStorage
from app.infrastructure.storage.minio import MinioStorage
from app.infrastructure.storage.provider import BaseStorageProvider, StorageProvider
from app.infrastructure.storage.s3 import S3Storage

logger = logging.getLogger(__name__)

__all__ = [
    "StorageProvider",
    "BaseStorageProvider",
    "MinioStorage",
    "S3Storage",
    "LocalStorage",
    "get_storage_provider",
    "clear_storage_cache",
]


@lru_cache(maxsize=1)
def get_storage_provider() -> MinioStorage | S3Storage | LocalStorage:
    """
    存储提供者工厂函数

    根据配置返回对应的存储提供者实例。
    使用 lru_cache 确保单例模式，避免重复创建连接。

    配置项 STORAGE_BACKEND 支持的值：
    - "minio": MinIO / S3 兼容存储（使用 minio-py SDK）
    - "s3": AWS S3（使用 boto3 SDK，也支持 S3 兼容服务）
    - "local": 本地文件存储

    Returns:
        StorageProvider: 存储提供者实例

    Raises:
        ValueError: 不支持的存储后端类型
    """
    backend = settings.STORAGE_BACKEND.lower()

    if backend == "minio":
        logger.info("初始化 MinIO 存储提供者")
        return MinioStorage(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE,
        )

    elif backend == "s3":
        logger.info("初始化 AWS S3 存储提供者")
        return S3Storage(
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            bucket=settings.AWS_S3_BUCKET,
            region=settings.AWS_S3_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )

    elif backend == "local":
        logger.info("初始化本地文件存储提供者")
        return LocalStorage(
            base_path=settings.LOCAL_STORAGE_PATH,
        )

    elif backend == "oss":
        raise NotImplementedError(
            "阿里云 OSS 存储暂未实现。"
            "请使用 STORAGE_BACKEND=minio, s3 或 local"
        )

    else:
        raise ValueError(
            f"不支持的存储后端类型: {backend}。"
            f"支持的类型: minio, s3, local"
        )


def clear_storage_cache() -> None:
    """
    清除存储提供者缓存

    用于在配置变更后重新初始化存储提供者。
    """
    get_storage_provider.cache_clear()
    logger.info("存储提供者缓存已清除")
