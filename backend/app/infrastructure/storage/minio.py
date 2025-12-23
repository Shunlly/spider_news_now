"""
MinIO / S3 兼容存储实现
MinIO / S3 Compatible Storage Implementation

支持 MinIO、AWS S3 及其他 S3 兼容的对象存储服务。
"""

import asyncio
import logging
from functools import partial

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.infrastructure.storage.provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class MinioStorage(BaseStorageProvider):
    """
    MinIO / S3 兼容存储实现

    使用 minio-py SDK 实现对象存储操作。
    支持 MinIO、AWS S3 及其他 S3 兼容服务。
    """

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        secure: bool | None = None,
    ):
        """
        初始化 MinIO 客户端

        Args:
            endpoint: MinIO 服务地址，如 "localhost:9000"
            access_key: 访问密钥
            secret_key: 密钥
            bucket: 存储桶名称
            secure: 是否使用 HTTPS
        """
        # 使用传入参数或从配置中读取
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket = bucket or settings.MINIO_BUCKET
        self.secure = secure if secure is not None else settings.MINIO_SECURE

        # 初始化 MinIO 客户端
        # 注意：minio-py 是同步库，需要在异步方法中使用 run_in_executor
        self._client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

        # 确保存储桶存在
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """
        确保存储桶存在，不存在则创建

        这是初始化时的同步操作，用于首次连接时创建存储桶。
        """
        try:
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket)
                logger.info(f"创建存储桶: {self.bucket}")
            else:
                logger.debug(f"存储桶已存在: {self.bucket}")
        except S3Error as e:
            logger.error(f"检查/创建存储桶失败: {e}")
            raise

    def _run_sync(self, func, *args, **kwargs):
        """
        在线程池中运行同步函数

        由于 minio-py 是同步库，需要将阻塞操作放入线程池执行。
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        上传文件到 MinIO

        Args:
            key: 存储键（对象名称）
            data: 文件二进制数据
            content_type: MIME 类型

        Returns:
            str: 文件的访问 URL
        """
        import io

        key = self.normalize_key(key)
        data_stream = io.BytesIO(data)
        data_length = len(data)

        try:
            # 在线程池中执行同步上传操作
            await self._run_sync(
                self._client.put_object,
                self.bucket,
                key,
                data_stream,
                data_length,
                content_type=content_type,
            )
            logger.info(f"文件上传成功: {key}, 大小: {data_length} bytes")
            return await self.get_public_url(key)
        except S3Error as e:
            logger.error(f"文件上传失败: {key}, 错误: {e}")
            raise

    async def download(self, key: str) -> bytes:
        """
        从 MinIO 下载文件

        Args:
            key: 存储键

        Returns:
            bytes: 文件二进制数据

        Raises:
            FileNotFoundError: 文件不存在
        """
        key = self.normalize_key(key)

        try:
            # 获取对象响应
            response = await self._run_sync(
                self._client.get_object,
                self.bucket,
                key,
            )
            try:
                data = response.read()
                logger.debug(f"文件下载成功: {key}, 大小: {len(data)} bytes")
                return data
            finally:
                response.close()
                response.release_conn()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"文件不存在: {key}") from None
            logger.error(f"文件下载失败: {key}, 错误: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """
        删除 MinIO 中的文件

        Args:
            key: 存储键

        Returns:
            bool: 删除成功返回 True
        """
        key = self.normalize_key(key)

        try:
            # 检查文件是否存在
            if not await self.exists(key):
                logger.debug(f"文件不存在，跳过删除: {key}")
                return False

            await self._run_sync(
                self._client.remove_object,
                self.bucket,
                key,
            )
            logger.info(f"文件删除成功: {key}")
            return True
        except S3Error as e:
            logger.error(f"文件删除失败: {key}, 错误: {e}")
            raise

    async def exists(self, key: str) -> bool:
        """
        检查文件是否存在于 MinIO

        Args:
            key: 存储键

        Returns:
            bool: 存在返回 True
        """
        key = self.normalize_key(key)

        try:
            await self._run_sync(
                self._client.stat_object,
                self.bucket,
                key,
            )
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise

    async def get_presigned_url(
        self,
        key: str,
        expires: int = 3600,
        method: str = "GET",
    ) -> str:
        """
        获取预签名 URL

        Args:
            key: 存储键
            expires: 过期时间（秒）
            method: HTTP 方法

        Returns:
            str: 预签名 URL
        """
        from datetime import timedelta

        key = self.normalize_key(key)

        try:
            if method.upper() == "GET":
                url = await self._run_sync(
                    self._client.presigned_get_object,
                    self.bucket,
                    key,
                    expires=timedelta(seconds=expires),
                )
            else:
                url = await self._run_sync(
                    self._client.presigned_put_object,
                    self.bucket,
                    key,
                    expires=timedelta(seconds=expires),
                )
            return url
        except S3Error as e:
            logger.error(f"获取预签名 URL 失败: {key}, 错误: {e}")
            raise

    async def get_public_url(self, key: str) -> str:
        """
        获取公开访问 URL

        注意：此 URL 仅在存储桶配置为公开访问时有效。
        对于私有存储桶，应使用 get_presigned_url。

        Args:
            key: 存储键

        Returns:
            str: 公开 URL
        """
        key = self.normalize_key(key)
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{self.bucket}/{key}"
