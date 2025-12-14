"""
本地文件存储实现
Local File Storage Implementation

用于开发和测试环境的本地文件存储。
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import aiofiles
import aiofiles.os

from app.core.config import settings
from app.storage.provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class LocalStorage(BaseStorageProvider):
    """
    本地文件存储实现

    将文件存储在本地文件系统中，适用于开发和测试环境。
    生产环境应使用 MinIO 或其他云存储服务。
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        初始化本地存储

        Args:
            base_path: 存储根目录，默认从配置读取
            base_url: 访问基础 URL，用于生成公开链接
        """
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self.base_url = base_url or "/storage"

        # 确保存储目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"本地存储初始化: {self.base_path}")

    def _get_full_path(self, key: str) -> Path:
        """获取文件的完整路径"""
        key = self.normalize_key(key)
        return self.base_path / key

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        上传文件到本地存储

        Args:
            key: 存储键（相对路径）
            data: 文件二进制数据
            content_type: MIME 类型（本地存储会忽略此参数）

        Returns:
            str: 文件的访问 URL
        """
        key = self.normalize_key(key)
        full_path = self._get_full_path(key)

        # 确保父目录存在
        await aiofiles.os.makedirs(full_path.parent, exist_ok=True)

        # 写入文件
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(data)

        logger.info(f"文件上传成功: {key}, 大小: {len(data)} bytes")
        return await self.get_public_url(key)

    async def download(self, key: str) -> bytes:
        """
        从本地存储下载文件

        Args:
            key: 存储键

        Returns:
            bytes: 文件二进制数据

        Raises:
            FileNotFoundError: 文件不存在
        """
        key = self.normalize_key(key)
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise FileNotFoundError(f"文件不存在: {key}")

        async with aiofiles.open(full_path, "rb") as f:
            data = await f.read()

        logger.debug(f"文件下载成功: {key}, 大小: {len(data)} bytes")
        return data

    async def delete(self, key: str) -> bool:
        """
        删除本地存储中的文件

        Args:
            key: 存储键

        Returns:
            bool: 删除成功返回 True
        """
        key = self.normalize_key(key)
        full_path = self._get_full_path(key)

        if not full_path.exists():
            logger.debug(f"文件不存在，跳过删除: {key}")
            return False

        await aiofiles.os.remove(full_path)
        logger.info(f"文件删除成功: {key}")

        # 尝试删除空的父目录
        await self._cleanup_empty_dirs(full_path.parent)

        return True

    async def _cleanup_empty_dirs(self, path: Path) -> None:
        """清理空目录"""
        try:
            while path != self.base_path:
                if path.exists() and not any(path.iterdir()):
                    path.rmdir()
                    path = path.parent
                else:
                    break
        except Exception as e:
            logger.debug(f"清理空目录失败: {e}")

    async def exists(self, key: str) -> bool:
        """
        检查文件是否存在

        Args:
            key: 存储键

        Returns:
            bool: 存在返回 True
        """
        key = self.normalize_key(key)
        full_path = self._get_full_path(key)
        return full_path.exists()

    async def get_presigned_url(
        self,
        key: str,
        expires: int = 3600,
        method: str = "GET",
    ) -> str:
        """
        获取预签名 URL

        注意：本地存储不支持真正的预签名 URL，
        此方法返回普通的公开 URL。
        在生产环境应使用支持预签名的存储服务。

        Args:
            key: 存储键
            expires: 过期时间（本地存储忽略此参数）
            method: HTTP 方法（本地存储忽略此参数）

        Returns:
            str: 公开 URL
        """
        logger.warning("本地存储不支持预签名 URL，返回公开 URL")
        return await self.get_public_url(key)

    async def get_public_url(self, key: str) -> str:
        """
        获取公开访问 URL

        Args:
            key: 存储键

        Returns:
            str: 公开 URL
        """
        key = self.normalize_key(key)
        # URL 编码路径中的特殊字符
        encoded_key = quote(key, safe="/")
        return f"{self.base_url}/{encoded_key}"
