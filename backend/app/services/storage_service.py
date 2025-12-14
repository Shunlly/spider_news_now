"""
存储服务包装器
Storage Service Wrapper

为应用服务提供统一的存储访问接口，封装底层存储提供者的细节。
遵循宪法 II.A 适配器模式。
"""

from typing import Optional

from app.core.logging import get_logger
from app.storage import StorageProvider, get_storage_provider

logger = get_logger(__name__)


class StorageService:
    """
    存储服务类

    封装存储提供者，提供高层次的存储操作接口。
    支持通过配置切换存储后端（MinIO/S3/本地）。
    """

    def __init__(self, provider: Optional[StorageProvider] = None):
        """
        初始化存储服务

        Args:
            provider: 存储提供者实例，默认从配置自动获取
        """
        self._provider = provider or get_storage_provider()
        self.logger = get_logger(__name__)

    @property
    def provider(self) -> StorageProvider:
        """获取底层存储提供者"""
        return self._provider

    async def upload(
        self,
        file_path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        上传文件

        Args:
            file_path: 存储路径（键）
            content: 文件内容
            content_type: MIME 类型

        Returns:
            文件的访问 URL
        """
        self.logger.debug(f"上传文件: {file_path}, 大小: {len(content)} bytes")
        return await self._provider.upload(file_path, content, content_type)

    async def download(self, file_path: str) -> bytes:
        """
        下载文件

        Args:
            file_path: 存储路径

        Returns:
            文件内容
        """
        self.logger.debug(f"下载文件: {file_path}")
        return await self._provider.download(file_path)

    async def delete(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 存储路径

        Returns:
            是否删除成功
        """
        self.logger.debug(f"删除文件: {file_path}")
        return await self._provider.delete(file_path)

    async def exists(self, file_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 存储路径

        Returns:
            是否存在
        """
        return await self._provider.exists(file_path)

    async def get_url(self, file_path: str, expires: int = 3600) -> str:
        """
        获取文件访问 URL

        Args:
            file_path: 存储路径
            expires: 过期时间（秒）

        Returns:
            访问 URL
        """
        return await self._provider.get_presigned_url(file_path, expires=expires)

    async def get_public_url(self, file_path: str) -> str:
        """
        获取公开访问 URL

        Args:
            file_path: 存储路径

        Returns:
            公开 URL
        """
        return await self._provider.get_public_url(file_path)


# 单例实例
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    获取存储服务单例

    Returns:
        StorageService 实例
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
