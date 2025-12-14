"""
存储提供者接口定义 - 遵循宪法 II.A 适配器模式
Storage Provider Interface - Following Constitution II.A Adapter Pattern

此模块定义了统一的存储接口，支持通过配置切换不同的存储后端：
- MinIO (S3 兼容)
- AWS S3
- 阿里云 OSS
- 本地文件系统
"""

from abc import ABC, abstractmethod
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class StorageProvider(Protocol):
    """
    存储提供者协议接口

    所有存储实现类必须实现此接口，确保可以通过配置无缝切换存储后端。
    遵循宪法 II.A 节的适配器模式要求：严禁硬编码具体存储实现。
    """

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        上传文件到存储

        Args:
            key: 存储键（路径），如 "media/2024/12/image.jpg"
            data: 文件二进制数据
            content_type: MIME 类型

        Returns:
            str: 文件的访问 URL
        """
        ...

    async def download(self, key: str) -> bytes:
        """
        从存储下载文件

        Args:
            key: 存储键

        Returns:
            bytes: 文件二进制数据

        Raises:
            FileNotFoundError: 文件不存在时抛出
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        删除存储中的文件

        Args:
            key: 存储键

        Returns:
            bool: 删除成功返回 True，文件不存在返回 False
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        检查文件是否存在

        Args:
            key: 存储键

        Returns:
            bool: 存在返回 True，不存在返回 False
        """
        ...

    async def get_presigned_url(
        self,
        key: str,
        expires: int = 3600,
        method: str = "GET",
    ) -> str:
        """
        获取预签名 URL（用于临时访问权限）

        Args:
            key: 存储键
            expires: 过期时间（秒），默认 1 小时
            method: HTTP 方法，GET 用于下载，PUT 用于上传

        Returns:
            str: 预签名 URL
        """
        ...

    async def get_public_url(self, key: str) -> str:
        """
        获取公开访问 URL（如果存储桶配置为公开）

        Args:
            key: 存储键

        Returns:
            str: 公开 URL
        """
        ...


class BaseStorageProvider(ABC):
    """
    存储提供者抽象基类

    提供通用的辅助方法，具体存储实现应继承此类。
    """

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """上传文件"""
        raise NotImplementedError

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """下载文件"""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除文件"""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        raise NotImplementedError

    @abstractmethod
    async def get_presigned_url(
        self,
        key: str,
        expires: int = 3600,
        method: str = "GET",
    ) -> str:
        """获取预签名 URL"""
        raise NotImplementedError

    @abstractmethod
    async def get_public_url(self, key: str) -> str:
        """获取公开 URL"""
        raise NotImplementedError

    def normalize_key(self, key: str) -> str:
        """
        规范化存储键，确保格式一致

        - 移除开头的斜杠
        - 将反斜杠转换为正斜杠
        - 移除多余的连续斜杠
        """
        # 替换反斜杠
        key = key.replace("\\", "/")
        # 移除开头斜杠
        key = key.lstrip("/")
        # 移除连续斜杠
        while "//" in key:
            key = key.replace("//", "/")
        return key

    def get_content_type(self, filename: str) -> str:
        """
        根据文件名推断 MIME 类型

        Args:
            filename: 文件名

        Returns:
            str: MIME 类型
        """
        import mimetypes
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"
