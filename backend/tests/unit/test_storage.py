"""
存储模块单元测试 - Storage Module Unit Tests
T034: StorageProvider (MinIO) tests

测试对象存储功能，使用 Mock 避免依赖实际服务。
"""

from unittest.mock import MagicMock, patch

import pytest

from app.storage.provider import BaseStorageProvider


class TestBaseStorageProvider:
    """BaseStorageProvider 基类测试"""

    def test_normalize_key_removes_leading_slash(self):
        """测试移除前导斜杠"""

        class DummyProvider(BaseStorageProvider):
            async def upload(self, key, data, content_type=""):
                return ""

            async def download(self, key):
                return b""

            async def delete(self, key):
                return True

            async def exists(self, key):
                return True

            async def get_presigned_url(self, key, expires=3600, method="GET"):
                return ""

            async def get_public_url(self, key):
                return ""

        provider = DummyProvider()

        # 测试移除前导斜杠
        assert provider.normalize_key("/path/to/file.txt") == "path/to/file.txt"
        assert provider.normalize_key("//double/slash.txt") == "double/slash.txt"
        assert provider.normalize_key("no/leading/slash.txt") == "no/leading/slash.txt"
        assert provider.normalize_key("/") == ""
        assert provider.normalize_key("") == ""


class TestMinioStorage:
    """MinIO 存储实现测试"""

    @pytest.fixture
    def mock_minio_client(self):
        """Mock MinIO 客户端"""
        with patch("app.storage.minio.Minio") as mock:
            mock_instance = MagicMock()
            mock_instance.bucket_exists.return_value = True
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_settings(self):
        """Mock 配置"""
        with patch("app.storage.minio.settings") as mock:
            mock.MINIO_ENDPOINT = "localhost:9000"
            mock.MINIO_ACCESS_KEY = "test_access_key"
            mock.MINIO_SECRET_KEY = "test_secret_key"
            mock.MINIO_BUCKET = "test-bucket"
            mock.MINIO_SECURE = False
            yield mock

    def test_minio_storage_init(self, mock_minio_client, mock_settings):
        """测试 MinIO 存储初始化"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        assert storage.endpoint == "localhost:9000"
        assert storage.bucket == "test-bucket"
        assert storage.secure is False

    def test_minio_storage_init_with_custom_params(self, mock_minio_client, mock_settings):
        """测试自定义参数初始化"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage(
            endpoint="custom:9001",
            access_key="custom_key",
            secret_key="custom_secret",
            bucket="custom-bucket",
            secure=True,
        )

        assert storage.endpoint == "custom:9001"
        assert storage.bucket == "custom-bucket"
        assert storage.secure is True

    def test_minio_creates_bucket_if_not_exists(self, mock_settings):
        """测试存储桶不存在时自动创建"""
        with patch("app.storage.minio.Minio") as mock_minio:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = False
            mock_minio.return_value = mock_client

            from app.storage.minio import MinioStorage

            MinioStorage()

            mock_client.make_bucket.assert_called_once_with("test-bucket")

    @pytest.mark.asyncio
    async def test_minio_upload(self, mock_minio_client, mock_settings):
        """测试文件上传"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # Mock put_object
        mock_minio_client.put_object.return_value = None

        result = await storage.upload(
            key="test/file.txt",
            data=b"test content",
            content_type="text/plain",
        )

        assert result is not None
        assert "test-bucket" in result
        assert "test/file.txt" in result

    @pytest.mark.asyncio
    async def test_minio_download(self, mock_minio_client, mock_settings):
        """测试文件下载"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # Mock get_object
        mock_response = MagicMock()
        mock_response.read.return_value = b"downloaded content"
        mock_minio_client.get_object.return_value = mock_response

        result = await storage.download("test/file.txt")

        assert result == b"downloaded content"
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_minio_exists_true(self, mock_minio_client, mock_settings):
        """测试文件存在检查 - 存在"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # Mock stat_object 成功
        mock_minio_client.stat_object.return_value = MagicMock()

        result = await storage.exists("existing/file.txt")

        assert result is True

    @pytest.mark.asyncio
    async def test_minio_exists_false(self, mock_minio_client, mock_settings):
        """测试文件存在检查 - 不存在"""
        from minio.error import S3Error

        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # Mock stat_object 抛出 NoSuchKey 错误
        error = S3Error(
            code="NoSuchKey",
            message="Object does not exist",
            resource="file.txt",
            request_id="req-123",
            host_id="host-456",
            response=None,
        )
        mock_minio_client.stat_object.side_effect = error

        result = await storage.exists("nonexistent/file.txt")

        assert result is False

    @pytest.mark.asyncio
    async def test_minio_delete(self, mock_minio_client, mock_settings):
        """测试文件删除"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # Mock stat_object 成功（文件存在）
        mock_minio_client.stat_object.return_value = MagicMock()
        mock_minio_client.remove_object.return_value = None

        result = await storage.delete("test/file.txt")

        assert result is True
        mock_minio_client.remove_object.assert_called()

    @pytest.mark.asyncio
    async def test_minio_get_presigned_url(self, mock_minio_client, mock_settings):
        """测试预签名 URL 生成"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # Mock presigned_get_object
        mock_minio_client.presigned_get_object.return_value = (
            "http://localhost:9000/test-bucket/file.txt?signature=abc"
        )

        result = await storage.get_presigned_url("test/file.txt", expires=7200)

        assert "signature" in result
        mock_minio_client.presigned_get_object.assert_called()

    @pytest.mark.asyncio
    async def test_minio_get_public_url(self, mock_minio_client, mock_settings):
        """测试公开 URL 生成"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        result = await storage.get_public_url("path/to/file.jpg")

        assert result == "http://localhost:9000/test-bucket/path/to/file.jpg"

    @pytest.mark.asyncio
    async def test_minio_get_public_url_https(self, mock_minio_client, mock_settings):
        """测试 HTTPS 公开 URL"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage(secure=True)

        result = await storage.get_public_url("path/to/file.jpg")

        assert result.startswith("https://")

    def test_normalize_key_integration(self, mock_minio_client, mock_settings):
        """测试 key 规范化集成"""
        from app.storage.minio import MinioStorage

        storage = MinioStorage()

        # 验证 normalize_key 被正确应用
        assert storage.normalize_key("/leading/slash/file.txt") == "leading/slash/file.txt"
        assert storage.normalize_key("no/slash/file.txt") == "no/slash/file.txt"


class TestStorageFactory:
    """存储工厂测试"""

    @pytest.fixture
    def mock_settings(self):
        """Mock 配置"""
        with patch("app.infrastructure.storage.settings") as mock:
            mock.MINIO_ENDPOINT = "localhost:9000"
            mock.MINIO_ACCESS_KEY = "test_access_key"
            mock.MINIO_SECRET_KEY = "test_secret_key"
            mock.MINIO_BUCKET = "test-bucket"
            mock.MINIO_SECURE = False
            mock.AWS_ACCESS_KEY_ID = None
            mock.AWS_SECRET_ACCESS_KEY = None
            mock.AWS_S3_BUCKET = None
            mock.AWS_S3_REGION = "us-east-1"
            mock.AWS_S3_ENDPOINT_URL = None
            mock.LOCAL_STORAGE_PATH = "./storage"
            yield mock

    def test_get_storage_provider_minio(self, mock_settings):
        """测试获取 MinIO 存储"""
        with patch("app.infrastructure.storage.minio.Minio") as mock_minio:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio.return_value = mock_client

            mock_settings.STORAGE_BACKEND = "minio"

            # 清除缓存以确保重新创建
            from app.storage import clear_storage_cache, get_storage_provider

            clear_storage_cache()

            storage = get_storage_provider()

            from app.infrastructure.storage.minio import MinioStorage

            assert isinstance(storage, MinioStorage)

    def test_get_storage_provider_singleton(self, mock_settings):
        """测试存储实例单例模式"""
        with patch("app.infrastructure.storage.minio.Minio") as mock_minio:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio.return_value = mock_client

            mock_settings.STORAGE_BACKEND = "minio"

            from app.storage import clear_storage_cache, get_storage_provider

            # 清除缓存以确保干净状态
            clear_storage_cache()

            storage1 = get_storage_provider()
            storage2 = get_storage_provider()

            # 应该返回同一个实例（lru_cache）
            assert storage1 is storage2
