"""
存储模块初始化
Storage Module Initialization

提供存储工厂函数，根据配置返回对应的存储提供者实例。
遵循宪法 II.A 适配器模式：通过配置切换存储后端，严禁硬编码。
"""

import logging
from functools import lru_cache
from typing import Union

from app.core.config import settings
from app.storage.local import LocalStorage
from app.storage.minio import MinioStorage
from app.storage.provider import BaseStorageProvider, StorageProvider

logger = logging.getLogger(__name__)

# 导出接口和实现类
__all__ = [
    "StorageProvider",
    "BaseStorageProvider",
    "MinioStorage",
    "LocalStorage",
    "get_storage_provider",
]


@lru_cache(maxsize=1)
def get_storage_provider() -> Union[MinioStorage, LocalStorage]:
    """
    存储提供者工厂函数

    根据配置返回对应的存储提供者实例。
    使用 lru_cache 确保单例模式，避免重复创建连接。

    配置项 STORAGE_BACKEND 支持的值：
    - "minio": MinIO / S3 兼容存储
    - "s3": AWS S3（使用 MinioStorage 实现）
    - "local": 本地文件存储

    Returns:
        StorageProvider: 存储提供者实例

    Raises:
        ValueError: 不支持的存储后端类型
    """
    backend = settings.STORAGE_BACKEND.lower()

    if backend in ("minio", "s3"):
        # MinIO 和 S3 使用相同的实现（S3 兼容）
        logger.info(f"初始化 {backend.upper()} 存储提供者")
        return MinioStorage(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE,
        )

    elif backend == "local":
        # 本地文件存储
        logger.info("初始化本地文件存储提供者")
        return LocalStorage(
            base_path=settings.LOCAL_STORAGE_PATH,
        )

    elif backend == "oss":
        # 阿里云 OSS - 暂未实现，抛出错误提示
        # 如需支持，可以在 app/storage/oss.py 中实现 OSSStorage 类
        raise NotImplementedError(
            "阿里云 OSS 存储暂未实现。"
            "请使用 STORAGE_BACKEND=minio 或 STORAGE_BACKEND=local"
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
