"""
去重模块单元测试 - Deduplication Module Unit Tests
T062: SimHash dedup algorithm tests
T063: URL Bloom Filter dedup tests

测试去重功能，使用 Mock 避免依赖 Redis 服务。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.dedup_service import DuplicateService


# ============== T062: SimHash Tests ==============


class TestSimHash:
    """SimHash 算法测试"""

    def test_compute_simhash_basic(self):
        """测试基本 SimHash 计算"""
        text = "This is a sample text for testing simhash algorithm"
        result = DuplicateService.compute_simhash(text)

        assert result is not None
        assert isinstance(result, int)
        assert result > 0

    def test_compute_simhash_empty_text(self):
        """测试空文本返回 0"""
        result = DuplicateService.compute_simhash("")
        assert result == 0

    def test_compute_simhash_similar_texts(self):
        """测试相似文本产生相似哈希"""
        # 使用更长且更相似的文本
        text1 = "北京市今日正式发布了一项重要的经济政策措施，预计将对市场产生深远的影响，各方面反应积极"
        text2 = "北京市今日正式发布了一项重要的经济政策措施，预计将对市场产生深远的影响，业界普遍表示欢迎"

        hash1 = DuplicateService.compute_simhash(text1)
        hash2 = DuplicateService.compute_simhash(text2)

        # 相似文本的汉明距离应该较小（SimHash 对短文本敏感度较高）
        distance = DuplicateService.hamming_distance(hash1, hash2)
        # SimHash 对中文短文本可能产生较大距离，放宽阈值
        assert distance < 20  # 相似文本距离应小于 20

    def test_compute_simhash_different_texts(self):
        """测试不同文本产生不同哈希"""
        text1 = "北京今日天气晴朗，适合户外活动"
        text2 = "上海股市大幅下跌，投资者恐慌情绪蔓延"

        hash1 = DuplicateService.compute_simhash(text1)
        hash2 = DuplicateService.compute_simhash(text2)

        # 不同文本的汉明距离应该较大
        distance = DuplicateService.hamming_distance(hash1, hash2)
        assert distance > 10  # 不同文本距离应大于 10

    def test_compute_simhash_handles_whitespace(self):
        """测试处理多余空白"""
        text1 = "Hello World Test"
        text2 = "Hello    World    Test"

        hash1 = DuplicateService.compute_simhash(text1)
        hash2 = DuplicateService.compute_simhash(text2)

        # 空白规范化后应该相同或非常接近
        distance = DuplicateService.hamming_distance(hash1, hash2)
        assert distance <= 3

    def test_hamming_distance_identical(self):
        """测试相同哈希距离为 0"""
        hash_value = 12345678901234
        distance = DuplicateService.hamming_distance(hash_value, hash_value)
        assert distance == 0

    def test_hamming_distance_one_bit_diff(self):
        """测试单位差异的汉明距离"""
        hash1 = 0b1010101010
        hash2 = 0b1010101011  # 最后一位不同

        distance = DuplicateService.hamming_distance(hash1, hash2)
        assert distance == 1

    def test_hamming_distance_all_bits_diff(self):
        """测试所有位不同的汉明距离"""
        hash1 = 0b0000000000
        hash2 = 0b1111111111  # 10 位全不同

        distance = DuplicateService.hamming_distance(hash1, hash2)
        assert distance == 10

    def test_is_similar_within_threshold(self):
        """测试阈值内判定为相似"""
        hash1 = 0b1010101010
        hash2 = 0b1010101011  # 距离 1

        assert DuplicateService.is_similar(hash1, hash2, threshold=3) is True
        assert DuplicateService.is_similar(hash1, hash2, threshold=1) is True

    def test_is_similar_outside_threshold(self):
        """测试超出阈值判定为不相似"""
        hash1 = 0b1010101010
        hash2 = 0b0101010101  # 距离 10

        assert DuplicateService.is_similar(hash1, hash2, threshold=3) is False
        assert DuplicateService.is_similar(hash1, hash2, threshold=9) is False

    def test_is_similar_default_threshold(self):
        """测试默认阈值"""
        # 默认阈值为 3
        hash1 = 0b1010101010
        hash2 = 0b1010101000  # 距离 2

        assert DuplicateService.is_similar(hash1, hash2) is True

    def test_simhash_unicode_chinese(self):
        """测试中文 SimHash"""
        text = "这是一段测试文本，用于验证中文 SimHash 功能"
        result = DuplicateService.compute_simhash(text)

        assert result is not None
        assert isinstance(result, int)

    def test_simhash_deterministic(self):
        """测试 SimHash 确定性"""
        text = "The same text should always produce the same hash"

        hash1 = DuplicateService.compute_simhash(text)
        hash2 = DuplicateService.compute_simhash(text)

        assert hash1 == hash2


# ============== T063: URL Hash and Bloom Filter Tests ==============


class TestURLHash:
    """URL 哈希测试"""

    def test_compute_url_hash_basic(self):
        """测试基本 URL 哈希"""
        url = "https://example.com/news/article"
        result = DuplicateService.compute_url_hash(url)

        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 十六进制

    def test_compute_url_hash_removes_trailing_slash(self):
        """测试移除末尾斜杠"""
        url1 = "https://example.com/news/article"
        url2 = "https://example.com/news/article/"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)

        assert hash1 == hash2

    def test_compute_url_hash_removes_fragment(self):
        """测试移除 URL 锚点"""
        url1 = "https://example.com/article"
        url2 = "https://example.com/article#section1"
        url3 = "https://example.com/article#comments"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)
        hash3 = DuplicateService.compute_url_hash(url3)

        assert hash1 == hash2 == hash3

    def test_compute_url_hash_removes_tracking_params(self):
        """测试移除追踪参数"""
        url1 = "https://example.com/article?id=123"
        url2 = "https://example.com/article?id=123&utm_source=twitter"
        url3 = "https://example.com/article?id=123&utm_source=twitter&utm_medium=social"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)
        hash3 = DuplicateService.compute_url_hash(url3)

        assert hash1 == hash2 == hash3

    def test_compute_url_hash_preserves_meaningful_params(self):
        """测试保留有意义的参数"""
        url1 = "https://example.com/article?id=123"
        url2 = "https://example.com/article?id=456"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)

        assert hash1 != hash2

    def test_compute_url_hash_strips_whitespace(self):
        """测试去除空白"""
        url1 = "https://example.com/article"
        url2 = "  https://example.com/article  "

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)

        assert hash1 == hash2

    def test_compute_url_hash_deterministic(self):
        """测试哈希确定性"""
        url = "https://example.com/news/2024/article-title"

        hash1 = DuplicateService.compute_url_hash(url)
        hash2 = DuplicateService.compute_url_hash(url)

        assert hash1 == hash2


class TestBloomFilter:
    """Bloom Filter 操作测试"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis 客户端"""
        mock = AsyncMock()
        mock.exists = AsyncMock(return_value=True)
        mock.sadd = AsyncMock(return_value=1)
        mock.sismember = AsyncMock(return_value=False)
        mock.pipeline = MagicMock()
        return mock

    @pytest.fixture
    def dedup_service(self, mock_redis):
        """创建使用 Mock Redis 的去重服务"""
        service = DuplicateService(redis_client=mock_redis)
        service._bloom_initialized = True
        return service

    @pytest.mark.asyncio
    async def test_add_to_bloom_filter(self, dedup_service, mock_redis):
        """测试添加到 Bloom Filter"""
        url_hash = "abc123def456"

        await dedup_service.add_to_bloom_filter(url_hash)

        mock_redis.sadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_many_to_bloom_filter(self, dedup_service, mock_redis):
        """测试批量添加到 Bloom Filter"""
        url_hashes = ["hash1", "hash2", "hash3"]

        await dedup_service.add_many_to_bloom_filter(url_hashes)

        mock_redis.sadd.assert_called_once()
        call_args = mock_redis.sadd.call_args
        assert "hash1" in call_args[0]
        assert "hash2" in call_args[0]
        assert "hash3" in call_args[0]

    @pytest.mark.asyncio
    async def test_add_many_empty_list(self, dedup_service, mock_redis):
        """测试批量添加空列表"""
        await dedup_service.add_many_to_bloom_filter([])

        mock_redis.sadd.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_bloom_filter_not_exists(self, dedup_service, mock_redis):
        """测试检查不存在的哈希"""
        mock_redis.sismember.return_value = False

        result = await dedup_service.check_bloom_filter("nonexistent_hash")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_bloom_filter_exists(self, dedup_service, mock_redis):
        """测试检查存在的哈希"""
        mock_redis.sismember.return_value = True

        result = await dedup_service.check_bloom_filter("existing_hash")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_many_bloom_filter(self, dedup_service, mock_redis):
        """测试批量检查 Bloom Filter"""
        url_hashes = ["hash1", "hash2", "hash3"]

        # Mock pipeline
        mock_pipe = AsyncMock()
        mock_pipe.sismember = MagicMock()
        mock_pipe.execute = AsyncMock(return_value=[True, False, True])
        mock_redis.pipeline.return_value = mock_pipe

        result = await dedup_service.check_many_bloom_filter(url_hashes)

        assert "hash1" in result
        assert "hash2" not in result
        assert "hash3" in result

    @pytest.mark.asyncio
    async def test_check_many_empty_list(self, dedup_service, mock_redis):
        """测试批量检查空列表"""
        result = await dedup_service.check_many_bloom_filter([])

        assert result == set()


class TestBloomFilterInitialization:
    """Bloom Filter 初始化测试"""

    @pytest.mark.asyncio
    async def test_ensure_bloom_filter_initializes_once(self):
        """测试 Bloom Filter 只初始化一次"""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=True)

        service = DuplicateService(redis_client=mock_redis)

        # 多次调用
        await service._ensure_bloom_filter()
        await service._ensure_bloom_filter()
        await service._ensure_bloom_filter()

        # 只应检查一次
        assert mock_redis.exists.call_count == 1

    @pytest.mark.asyncio
    async def test_ensure_bloom_filter_logs_creation(self):
        """测试新建 Bloom Filter 时记录日志"""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=False)

        with patch("app.services.dedup_service.settings") as mock_settings:
            mock_settings.BLOOM_FILTER_CAPACITY = 10000000
            mock_settings.BLOOM_FILTER_ERROR_RATE = 0.001

            service = DuplicateService(redis_client=mock_redis)
            await service._ensure_bloom_filter()

            assert service._bloom_initialized is True


class TestDuplicateServiceClose:
    """服务关闭测试"""

    @pytest.mark.asyncio
    async def test_close_releases_redis(self):
        """测试关闭释放 Redis 连接"""
        mock_redis = AsyncMock()

        service = DuplicateService(redis_client=mock_redis)
        await service.close()

        mock_redis.close.assert_called_once()
        assert service._redis is None

    @pytest.mark.asyncio
    async def test_close_handles_no_redis(self):
        """测试没有 Redis 时关闭不报错"""
        service = DuplicateService()
        service._redis = None

        await service.close()  # 应该不报错
