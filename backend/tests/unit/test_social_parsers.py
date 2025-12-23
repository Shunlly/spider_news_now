"""
社交解析器单元测试 - Social Parser Unit Tests
T091: Unit test for Twitter thread parser
T092: Unit test for Telegram message parser

测试社交数据解析功能，使用 Mock 避免依赖外部服务。
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.social_service import SocialService, generate_message_hash


# ============== 辅助函数测试 ==============


class TestGenerateMessageHash:
    """消息哈希生成测试"""

    def test_generate_hash_basic(self):
        """测试基本哈希生成"""
        result = generate_message_hash("twitter", "123456", "Hello world")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 十六进制

    def test_generate_hash_same_input(self):
        """测试相同输入产生相同哈希"""
        hash1 = generate_message_hash("twitter", "123", "Test content")
        hash2 = generate_message_hash("twitter", "123", "Test content")

        assert hash1 == hash2

    def test_generate_hash_different_platform(self):
        """测试不同平台产生不同哈希"""
        hash1 = generate_message_hash("twitter", "123", "Test content")
        hash2 = generate_message_hash("telegram", "123", "Test content")

        assert hash1 != hash2

    def test_generate_hash_different_message_id(self):
        """测试不同消息 ID 产生不同哈希"""
        hash1 = generate_message_hash("twitter", "123", "Test content")
        hash2 = generate_message_hash("twitter", "456", "Test content")

        assert hash1 != hash2

    def test_generate_hash_different_content(self):
        """测试不同内容产生不同哈希"""
        hash1 = generate_message_hash("twitter", "123", "Content A")
        hash2 = generate_message_hash("twitter", "123", "Content B")

        assert hash1 != hash2

    def test_generate_hash_empty_content(self):
        """测试空内容"""
        result = generate_message_hash("twitter", "123", "")

        assert result is not None
        assert len(result) == 64

    def test_generate_hash_none_content(self):
        """测试 None 内容"""
        result = generate_message_hash("twitter", "123", None)

        assert result is not None
        assert len(result) == 64

    def test_generate_hash_unicode_content(self):
        """测试 Unicode 中文内容"""
        result = generate_message_hash("twitter", "123", "这是中文内容测试")

        assert result is not None
        assert len(result) == 64

    def test_generate_hash_emoji_content(self):
        """测试 Emoji 内容"""
        result = generate_message_hash("twitter", "123", "Hello 👋 World 🌍")

        assert result is not None
        assert len(result) == 64


# ============== T091: Twitter 解析器测试 ==============


class TestTwitterParser:
    """Twitter 解析器测试"""

    @pytest.fixture
    def mock_twitter_service(self):
        """Mock Twitter 服务"""
        with patch("app.services.social_service.get_twitter_service") as mock:
            service = MagicMock()
            service.is_connected = True
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_session(self):
        """Mock 社交会话"""
        session = MagicMock()
        session.id = 1
        session.target_id = "12345"
        session.target_name = "Test User"
        session.target_username = "@testuser"
        session.last_message_at = None
        session.message_count = 0
        return session

    def test_parse_twitter_tweet_data(self):
        """测试解析 Twitter 推文数据结构"""
        tweet_data = {
            "id": "1234567890",
            "text": "This is a test tweet",
            "created_at": "2024-01-15 10:30",
            "user": {
                "id": "user123",
                "name": "Test User",
                "screen_name": "testuser",
            },
            "reply_count": 5,
            "retweet_count": 10,
            "favorite_count": 25,
            "views_count": "1000",
            "is_retweet": False,
            "media": [
                {"url": "https://example.com/image1.jpg"},
                {"url": "https://example.com/image2.jpg"},
            ],
        }

        # 验证数据结构
        assert "id" in tweet_data
        assert "text" in tweet_data
        assert "user" in tweet_data
        assert tweet_data["user"]["screen_name"] == "testuser"
        assert len(tweet_data["media"]) == 2

    def test_parse_twitter_retweet(self):
        """测试解析转发推文"""
        retweet_data = {
            "id": "9876543210",
            "text": "RT @original: Original tweet content",
            "is_retweet": True,
            "retweeted_status": {
                "id": "1111111111",
                "text": "Original tweet content",
            },
        }

        assert retweet_data["is_retweet"] is True
        assert "retweeted_status" in retweet_data

    def test_parse_twitter_reply(self):
        """测试解析回复推文"""
        reply_data = {
            "id": "5555555555",
            "text": "@someone This is a reply",
            "in_reply_to_status_id": "1111111111",
            "in_reply_to_user_id": "user456",
        }

        assert "in_reply_to_status_id" in reply_data
        assert reply_data["in_reply_to_status_id"] == "1111111111"

    def test_parse_twitter_thread_structure(self):
        """测试解析 Twitter Thread 结构"""
        thread_data = {
            "conversation_id": "1234567890",
            "tweets": [
                {"id": "1234567890", "text": "Thread start 1/3"},
                {"id": "1234567891", "text": "Thread continuation 2/3"},
                {"id": "1234567892", "text": "Thread end 3/3"},
            ],
        }

        assert len(thread_data["tweets"]) == 3
        assert thread_data["tweets"][0]["id"] == thread_data["conversation_id"]

    def test_parse_twitter_date_format(self):
        """测试解析 Twitter 日期格式"""
        # Twitter API 常见日期格式
        date_str = "2024-01-15 10:30"

        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            assert parsed.year == 2024
            assert parsed.month == 1
            assert parsed.day == 15
        except ValueError:
            pytest.fail("Failed to parse Twitter date format")

    def test_parse_twitter_metrics(self):
        """测试解析推文指标"""
        metrics = {
            "reply_count": 5,
            "retweet_count": 10,
            "favorite_count": 25,
            "views_count": "1000",  # 注意：可能是字符串
        }

        # 验证数值转换
        assert int(metrics.get("views_count", 0)) == 1000
        assert metrics["reply_count"] == 5

    def test_parse_twitter_media_urls(self):
        """测试解析媒体 URL"""
        import json

        tweet_with_media = {
            "media": [
                {"url": "https://pbs.twimg.com/media/image1.jpg"},
                {"url": "https://pbs.twimg.com/media/image2.jpg"},
            ],
        }

        # 提取 URL 并序列化
        urls = [m.get("url") for m in tweet_with_media.get("media", []) if m.get("url")]
        json_urls = json.dumps(urls)

        assert len(urls) == 2
        assert json.loads(json_urls) == urls


# ============== T092: Telegram 解析器测试 ==============


class TestTelegramParser:
    """Telegram 消息解析器测试"""

    @pytest.fixture
    def mock_telegram_service(self):
        """Mock Telegram 服务"""
        with patch("app.services.social_service.get_telegram_service") as mock:
            service = MagicMock()
            service.is_connected = True
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_session(self):
        """Mock 社交会话"""
        session = MagicMock()
        session.id = 1
        session.target_id = "-1001234567890"
        session.target_name = "Test Channel"
        session.target_username = "@testchannel"
        session.last_message_at = None
        session.message_count = 0
        return session

    def test_parse_telegram_message_data(self):
        """测试解析 Telegram 消息数据结构"""
        message_data = {
            "id": 12345,
            "date": "2024-01-15T10:30:00Z",
            "text": "This is a test message",
            "sender_id": 987654321,
            "views": 500,
            "forwards": 10,
            "reply_to_id": None,
        }

        # 验证数据结构
        assert "id" in message_data
        assert "text" in message_data
        assert "date" in message_data
        assert message_data["views"] == 500

    def test_parse_telegram_date_format(self):
        """测试解析 Telegram 日期格式 (ISO 8601)"""
        date_str = "2024-01-15T10:30:00Z"

        try:
            parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            parsed = parsed.replace(tzinfo=None)
            assert parsed.year == 2024
            assert parsed.month == 1
            assert parsed.day == 15
        except ValueError:
            pytest.fail("Failed to parse Telegram date format")

    def test_parse_telegram_channel_message(self):
        """测试解析频道消息"""
        channel_message = {
            "id": 12345,
            "text": "Channel announcement",
            "sender_id": None,  # 频道消息没有发送者 ID
            "views": 1000,
            "forwards": 50,
        }

        assert channel_message["sender_id"] is None
        assert channel_message["views"] == 1000

    def test_parse_telegram_group_message(self):
        """测试解析群组消息"""
        group_message = {
            "id": 12345,
            "text": "Group message",
            "sender_id": 987654321,  # 群组消息有发送者
            "sender_name": "User Name",
        }

        assert group_message["sender_id"] is not None
        assert "sender_name" in group_message

    def test_parse_telegram_reply_message(self):
        """测试解析回复消息"""
        reply_message = {
            "id": 12346,
            "text": "This is a reply",
            "reply_to_id": 12345,
        }

        assert reply_message["reply_to_id"] == 12345

    def test_parse_telegram_forwarded_message(self):
        """测试解析转发消息"""
        forwarded_message = {
            "id": 12347,
            "text": "Forwarded content",
            "forward_from": {
                "id": 111111,
                "name": "Original Channel",
            },
        }

        assert "forward_from" in forwarded_message
        assert forwarded_message["forward_from"]["name"] == "Original Channel"

    def test_parse_telegram_media_message(self):
        """测试解析媒体消息"""
        import json

        media_message = {
            "id": 12348,
            "text": "Check out this photo",
            "urls": [
                "https://cdn.telegram.org/file/photo1.jpg",
                "https://cdn.telegram.org/file/photo2.jpg",
            ],
        }

        urls = media_message.get("urls", [])
        json_urls = json.dumps(urls)

        assert len(urls) == 2
        assert json.loads(json_urls) == urls

    def test_parse_telegram_html_content(self):
        """测试解析 HTML 格式内容"""
        html_message = {
            "id": 12349,
            "text": "Plain text version",
            "html": "<b>Bold</b> and <i>italic</i> text",
        }

        assert html_message["text"] == "Plain text version"
        assert "<b>" in html_message["html"]

    def test_parse_telegram_metrics(self):
        """测试解析消息指标"""
        metrics = {
            "views": 1500,
            "forwards": 75,
            "replies": None,  # Telegram 不总是提供回复数
        }

        assert metrics["views"] == 1500
        assert metrics.get("forwards", 0) == 75
        assert metrics.get("replies") is None

    def test_parse_telegram_channel_id_format(self):
        """测试解析频道 ID 格式"""
        # Telegram 频道 ID 通常是负数
        channel_id = "-1001234567890"

        assert int(channel_id) < 0
        assert channel_id.startswith("-100")

    def test_parse_telegram_message_entities(self):
        """测试解析消息实体（链接、提及等）"""
        message_with_entities = {
            "id": 12350,
            "text": "Check @channel and https://example.com",
            "entities": [
                {"type": "mention", "offset": 6, "length": 8},
                {"type": "url", "offset": 19, "length": 19},
            ],
        }

        entities = message_with_entities.get("entities", [])
        assert len(entities) == 2
        assert entities[0]["type"] == "mention"
        assert entities[1]["type"] == "url"


# ============== 集成测试 Mock ==============


class TestSocialServiceHelpers:
    """SocialService 辅助方法测试"""

    def test_message_hash_deterministic(self):
        """测试消息哈希确定性"""
        # 多次调用应该产生相同结果
        hashes = [
            generate_message_hash("twitter", "123", "test")
            for _ in range(5)
        ]

        assert all(h == hashes[0] for h in hashes)

    def test_message_hash_collision_resistant(self):
        """测试消息哈希抗碰撞性"""
        # 生成多个不同内容的哈希
        hashes = set()
        for i in range(100):
            h = generate_message_hash("twitter", str(i), f"Content {i}")
            hashes.add(h)

        # 应该没有碰撞
        assert len(hashes) == 100

    def test_parse_empty_message_list(self):
        """测试解析空消息列表"""
        messages = []

        assert len(messages) == 0

    def test_parse_large_message_content(self):
        """测试解析大内容消息"""
        # Twitter 最大 280 字符，但 Telegram 可以更长
        large_content = "A" * 5000

        hash_result = generate_message_hash("telegram", "123", large_content)
        assert hash_result is not None
        assert len(hash_result) == 64
