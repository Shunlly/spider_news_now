"""
AWS S3 存储实现
AWS S3 Storage Implementation

使用 boto3 SDK 实现 AWS S3 对象存储操作。
支持 AWS S3 及兼容 S3 API 的服务（通过 endpoint_url 配置）。
"""

import asyncio
import logging
from functools import partial
from typing import Any

from app.core.config import settings
from app.infrastructure.storage.provider import BaseStorageProvider

logger = logging.getLogger(__name__)


class S3Storage(BaseStorageProvider):
    """
    AWS S3 存储实现

    使用 boto3 SDK 实现对象存储操作。
    支持 AWS S3 及其他 S3 兼容服务（如 MinIO、DigitalOcean Spaces）。

    配置优先级：
    1. 构造函数参数
    2. AWS_* 环境变量
    3. MINIO_* 环境变量（向后兼容）
    """

    def __init__(
        self,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
    ):
        """
        初始化 S3 客户端

        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            bucket: 存储桶名称
            region: AWS 区域，如 "us-east-1"
            endpoint_url: 自定义端点 URL（用于 S3 兼容服务）
        """
        # 配置优先级：参数 > AWS_* > MINIO_*
        self.access_key_id = (
            access_key_id
            or settings.AWS_ACCESS_KEY_ID
            or settings.MINIO_ACCESS_KEY
        )
        self.secret_access_key = (
            secret_access_key
            or settings.AWS_SECRET_ACCESS_KEY
            or settings.MINIO_SECRET_KEY
        )
        self.bucket = (
            bucket
            or settings.AWS_S3_BUCKET
            or settings.MINIO_BUCKET
        )
        self.region = region or settings.AWS_S3_REGION

        # 处理 endpoint_url：支持 S3 兼容服务
        if endpoint_url:
            self.endpoint_url = endpoint_url
        elif settings.AWS_S3_ENDPOINT_URL:
            self.endpoint_url = settings.AWS_S3_ENDPOINT_URL
        elif settings.MINIO_ENDPOINT:
            # 从 MinIO 配置构建 endpoint_url
            protocol = "https" if settings.MINIO_SECURE else "http"
            self.endpoint_url = f"{protocol}://{settings.MINIO_ENDPOINT}"
        else:
            self.endpoint_url = None  # 使用 AWS 默认端点

        # 延迟初始化客户端（首次使用时创建）
        self._client: Any = None
        self._initialized = False

    def _get_client(self) -> Any:
        """
        获取 boto3 S3 客户端（延迟初始化）

        Returns:
            boto3.client: S3 客户端实例
        """
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config
            except ImportError as e:
                raise ImportError(
                    "boto3 未安装。请运行 'pip install boto3' 安装依赖。"
                ) from e

            # 配置 boto3 客户端
            config = Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            )

            client_kwargs = {
                "service_name": "s3",
                "aws_access_key_id": self.access_key_id,
                "aws_secret_access_key": self.secret_access_key,
                "region_name": self.region,
                "config": config,
            }

            # 添加自定义端点（用于 S3 兼容服务）
            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url

            self._client = boto3.client(**client_kwargs)

            # 确保存储桶存在
            self._ensure_bucket()

        return self._client

    def _ensure_bucket(self) -> None:
        """
        确保存储桶存在，不存在则创建

        注意：仅在非 AWS S3 环境（即使用自定义 endpoint）时自动创建存储桶。
        AWS S3 存储桶创建需要特殊权限，建议手动创建。
        """
        from botocore.exceptions import ClientError

        try:
            self._client.head_bucket(Bucket=self.bucket)
            logger.debug(f"存储桶已存在: {self.bucket}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchBucket"):
                # 仅在使用自定义端点时自动创建存储桶
                if self.endpoint_url:
                    try:
                        self._client.create_bucket(Bucket=self.bucket)
                        logger.info(f"创建存储桶: {self.bucket}")
                    except ClientError as create_error:
                        logger.error(f"创建存储桶失败: {create_error}")
                        raise
                else:
                    logger.warning(
                        f"存储桶 {self.bucket} 不存在。"
                        f"请在 AWS 控制台手动创建存储桶。"
                    )
            elif error_code in ("403", "AccessDenied"):
                logger.warning(
                    f"无权限检查存储桶 {self.bucket}，假设存储桶已存在。"
                )
            else:
                logger.error(f"检查存储桶失败: {e}")
                raise

    def _run_sync(self, func, *args, **kwargs):
        """
        在线程池中运行同步函数

        由于 boto3 是同步库，需要将阻塞操作放入线程池执行。
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
        上传文件到 S3

        Args:
            key: 存储键（对象名称）
            data: 文件二进制数据
            content_type: MIME 类型

        Returns:
            str: 文件的访问 URL
        """
        from botocore.exceptions import ClientError

        key = self.normalize_key(key)
        client = self._get_client()

        try:
            await self._run_sync(
                client.put_object,
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.info(f"文件上传成功: {key}, 大小: {len(data)} bytes")
            return await self.get_public_url(key)
        except ClientError as e:
            logger.error(f"文件上传失败: {key}, 错误: {e}")
            raise

    async def download(self, key: str) -> bytes:
        """
        从 S3 下载文件

        Args:
            key: 存储键

        Returns:
            bytes: 文件二进制数据

        Raises:
            FileNotFoundError: 文件不存在
        """
        from botocore.exceptions import ClientError

        key = self.normalize_key(key)
        client = self._get_client()

        try:
            response = await self._run_sync(
                client.get_object,
                Bucket=self.bucket,
                Key=key,
            )
            # 读取响应体
            body = response["Body"]
            data = await self._run_sync(body.read)
            logger.debug(f"文件下载成功: {key}, 大小: {len(data)} bytes")
            return data
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                raise FileNotFoundError(f"文件不存在: {key}") from None
            logger.error(f"文件下载失败: {key}, 错误: {e}")
            raise

    async def delete(self, key: str) -> bool:
        """
        删除 S3 中的文件

        Args:
            key: 存储键

        Returns:
            bool: 删除成功返回 True，文件不存在返回 False
        """
        from botocore.exceptions import ClientError

        key = self.normalize_key(key)
        client = self._get_client()

        # 检查文件是否存在
        if not await self.exists(key):
            logger.debug(f"文件不存在，跳过删除: {key}")
            return False

        try:
            await self._run_sync(
                client.delete_object,
                Bucket=self.bucket,
                Key=key,
            )
            logger.info(f"文件删除成功: {key}")
            return True
        except ClientError as e:
            logger.error(f"文件删除失败: {key}, 错误: {e}")
            raise

    async def exists(self, key: str) -> bool:
        """
        检查文件是否存在于 S3

        Args:
            key: 存储键

        Returns:
            bool: 存在返回 True
        """
        from botocore.exceptions import ClientError

        key = self.normalize_key(key)
        client = self._get_client()

        try:
            await self._run_sync(
                client.head_object,
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
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
            expires: 过期时间（秒），默认 1 小时
            method: HTTP 方法，GET 用于下载，PUT 用于上传

        Returns:
            str: 预签名 URL
        """
        from botocore.exceptions import ClientError

        key = self.normalize_key(key)
        client = self._get_client()

        try:
            if method.upper() == "GET":
                url = await self._run_sync(
                    client.generate_presigned_url,
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires,
                )
            else:
                url = await self._run_sync(
                    client.generate_presigned_url,
                    "put_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires,
                )
            return url
        except ClientError as e:
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

        if self.endpoint_url:
            # 自定义端点（S3 兼容服务）
            return f"{self.endpoint_url}/{self.bucket}/{key}"
        else:
            # AWS S3 标准 URL 格式
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict]:
        """
        列出存储桶中的对象

        Args:
            prefix: 键前缀过滤
            max_keys: 最大返回数量

        Returns:
            list[dict]: 对象列表，每个对象包含 key, size, last_modified
        """
        from botocore.exceptions import ClientError

        client = self._get_client()
        prefix = self.normalize_key(prefix) if prefix else ""

        try:
            response = await self._run_sync(
                client.list_objects_v2,
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            objects = []
            for obj in response.get("Contents", []):
                objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                })
            return objects
        except ClientError as e:
            logger.error(f"列出对象失败: {e}")
            raise

    async def copy_object(
        self,
        source_key: str,
        dest_key: str,
    ) -> str:
        """
        复制对象

        Args:
            source_key: 源对象键
            dest_key: 目标对象键

        Returns:
            str: 目标对象的 URL
        """
        from botocore.exceptions import ClientError

        source_key = self.normalize_key(source_key)
        dest_key = self.normalize_key(dest_key)
        client = self._get_client()

        try:
            await self._run_sync(
                client.copy_object,
                Bucket=self.bucket,
                CopySource={"Bucket": self.bucket, "Key": source_key},
                Key=dest_key,
            )
            logger.info(f"对象复制成功: {source_key} -> {dest_key}")
            return await self.get_public_url(dest_key)
        except ClientError as e:
            logger.error(f"对象复制失败: {e}")
            raise
