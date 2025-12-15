"""
Tests for Social Media Scrapers.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.social_session import Platform, SessionStatus, SocialSession, TargetType
from app.scrapers.twitter_scraper import TwitterScraper
from app.scrapers.telegram_scraper import TelegramScraper


class TestTwitterScraper:
    """Test cases for Twitter scraper."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock social session."""
        session = MagicMock(spec=SocialSession)
        session.id = 1
        session.session_key = "twitter:user:123456789"
        session.platform = Platform.TWITTER
        session.target_type = TargetType.USER
        session.target_id = "123456789"
        session.target_name = "Test User"
        session.status = SessionStatus.ACTIVE
        session.message_count = 0
        return session

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def scraper(self, mock_session, mock_db):
        """Create a Twitter scraper instance."""
        return TwitterScraper(
            session=mock_session,
            db=mock_db,
            bearer_token="test_bearer_token",
        )

    def test_scraper_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.platform == Platform.TWITTER
        assert scraper.bearer_token == "test_bearer_token"
        assert scraper.BASE_URL == "https://api.twitter.com/2"

    def test_tweet_fields_configured(self, scraper):
        """Test that tweet fields are properly configured."""
        assert "id" in scraper.TWEET_FIELDS
        assert "text" in scraper.TWEET_FIELDS
        assert "created_at" in scraper.TWEET_FIELDS
        assert "public_metrics" in scraper.TWEET_FIELDS

    def test_user_fields_configured(self, scraper):
        """Test that user fields are properly configured."""
        assert "id" in scraper.USER_FIELDS
        assert "name" in scraper.USER_FIELDS
        assert "username" in scraper.USER_FIELDS

    @pytest.mark.asyncio
    async def test_parse_message_basic(self, scraper):
        """Test parsing a basic tweet."""
        raw_tweet = {
            "id": "1234567890",
            "text": "Hello, world!",
            "author_id": "123456789",
            "created_at": "2024-01-15T12:00:00.000Z",
            "public_metrics": {
                "reply_count": 5,
                "retweet_count": 10,
                "like_count": 100,
                "impression_count": 1000,
            },
        }

        # Add author to cache
        scraper._users_cache["123456789"] = {
            "id": "123456789",
            "name": "Test User",
            "username": "testuser",
        }

        result = await scraper.parse_message(raw_tweet)

        assert result["message_id"] == "1234567890"
        assert result["content"] == "Hello, world!"
        assert result["author_id"] == "123456789"
        assert result["author_name"] == "Test User"
        assert result["author_username"] == "testuser"
        assert result["reply_count"] == 5
        assert result["repost_count"] == 10
        assert result["like_count"] == 100
        assert result["view_count"] == 1000

    @pytest.mark.asyncio
    async def test_parse_message_with_media(self, scraper):
        """Test parsing a tweet with media."""
        raw_tweet = {
            "id": "1234567890",
            "text": "Check this out!",
            "author_id": "123456789",
            "created_at": "2024-01-15T12:00:00.000Z",
            "attachments": {
                "media_keys": ["media_key_1", "media_key_2"],
            },
            "public_metrics": {
                "reply_count": 0,
                "retweet_count": 0,
                "like_count": 0,
                "impression_count": 0,
            },
        }

        # Add media to cache
        scraper._media_cache["media_key_1"] = {
            "media_key": "media_key_1",
            "type": "photo",
            "url": "https://pbs.twimg.com/media/photo1.jpg",
        }
        scraper._media_cache["media_key_2"] = {
            "media_key": "media_key_2",
            "type": "video",
            "preview_image_url": "https://pbs.twimg.com/media/video1_thumb.jpg",
        }

        scraper._users_cache["123456789"] = {"name": "Test", "username": "test"}

        result = await scraper.parse_message(raw_tweet)

        assert len(result["media_urls"]) == 2
        assert "https://pbs.twimg.com/media/photo1.jpg" in result["media_urls"]

    @pytest.mark.asyncio
    async def test_parse_message_with_reply(self, scraper):
        """Test parsing a reply tweet."""
        raw_tweet = {
            "id": "1234567890",
            "text": "@user2 Great post!",
            "author_id": "123456789",
            "created_at": "2024-01-15T12:00:00.000Z",
            "referenced_tweets": [
                {"type": "replied_to", "id": "9876543210"},
            ],
            "public_metrics": {
                "reply_count": 0,
                "retweet_count": 0,
                "like_count": 0,
                "impression_count": 0,
            },
        }

        scraper._users_cache["123456789"] = {"name": "Test", "username": "test"}

        result = await scraper.parse_message(raw_tweet)

        assert result["reply_to_id"] == "9876543210"
        assert result["repost_of_id"] is None

    @pytest.mark.asyncio
    async def test_parse_message_retweet(self, scraper):
        """Test parsing a retweet."""
        raw_tweet = {
            "id": "1234567890",
            "text": "RT @original: Original tweet text",
            "author_id": "123456789",
            "created_at": "2024-01-15T12:00:00.000Z",
            "referenced_tweets": [
                {"type": "retweeted", "id": "1111111111"},
            ],
            "public_metrics": {
                "reply_count": 0,
                "retweet_count": 0,
                "like_count": 0,
                "impression_count": 0,
            },
        }

        scraper._users_cache["123456789"] = {"name": "Test", "username": "test"}

        result = await scraper.parse_message(raw_tweet)

        assert result["repost_of_id"] == "1111111111"

    def test_compute_message_hash(self, scraper):
        """Test message hash computation."""
        hash1 = scraper.compute_message_hash("12345")
        hash2 = scraper.compute_message_hash("12345")
        hash3 = scraper.compute_message_hash("67890")

        assert hash1 == hash2  # Same input gives same hash
        assert hash1 != hash3  # Different input gives different hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters


class TestTelegramScraper:
    """Test cases for Telegram scraper."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock social session."""
        session = MagicMock(spec=SocialSession)
        session.id = 1
        session.session_key = "telegram:channel:-1001234567890"
        session.platform = Platform.TELEGRAM
        session.target_type = TargetType.CHANNEL
        session.target_id = "-1001234567890"
        session.target_name = "Test Channel"
        session.status = SessionStatus.ACTIVE
        session.message_count = 0
        return session

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def scraper(self, mock_session, mock_db):
        """Create a Telegram scraper instance."""
        return TelegramScraper(
            session=mock_session,
            db=mock_db,
            bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        )

    def test_scraper_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.platform == Platform.TELEGRAM
        assert scraper.BASE_URL == "https://api.telegram.org"

    def test_api_url_property(self, scraper):
        """Test API URL generation."""
        assert scraper.api_url.startswith("https://api.telegram.org/bot")
        assert "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" in scraper.api_url

    @pytest.mark.asyncio
    async def test_parse_message_basic(self, scraper):
        """Test parsing a basic Telegram message."""
        raw_message = {
            "message_id": 12345,
            "from": {
                "id": 987654321,
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
            },
            "text": "Hello from Telegram!",
            "date": 1705320000,  # Unix timestamp
        }

        result = await scraper.parse_message(raw_message)

        assert result["message_id"] == "12345"
        assert result["content"] == "Hello from Telegram!"
        assert result["author_id"] == "987654321"
        assert result["author_name"] == "Test User"
        assert result["author_username"] == "testuser"

    @pytest.mark.asyncio
    async def test_parse_message_from_channel(self, scraper):
        """Test parsing a message from channel (sender_chat)."""
        raw_message = {
            "message_id": 12345,
            "sender_chat": {
                "id": -1001234567890,
                "title": "Test Channel",
            },
            "text": "Channel announcement",
            "date": 1705320000,
            "views": 5000,
        }

        result = await scraper.parse_message(raw_message)

        assert result["author_name"] == "Test Channel"
        assert result["view_count"] == 5000

    @pytest.mark.asyncio
    async def test_parse_message_with_photo(self, scraper):
        """Test parsing a message with photo."""
        raw_message = {
            "message_id": 12345,
            "from": {"id": 123, "first_name": "Test"},
            "caption": "Check this photo!",
            "date": 1705320000,
            "photo": [
                {"file_id": "small_photo_id", "file_size": 1000},
                {"file_id": "medium_photo_id", "file_size": 5000},
                {"file_id": "large_photo_id", "file_size": 10000},
            ],
        }

        result = await scraper.parse_message(raw_message)

        assert result["content"] == "Check this photo!"
        assert len(result["media_urls"]) == 1
        assert "large_photo_id" in result["media_urls"][0]

    @pytest.mark.asyncio
    async def test_parse_message_with_reply(self, scraper):
        """Test parsing a reply message."""
        raw_message = {
            "message_id": 12345,
            "from": {"id": 123, "first_name": "Test"},
            "text": "This is a reply",
            "date": 1705320000,
            "reply_to_message": {
                "message_id": 12344,
            },
        }

        result = await scraper.parse_message(raw_message)

        assert result["reply_to_id"] == "12344"

    @pytest.mark.asyncio
    async def test_parse_message_forwarded(self, scraper):
        """Test parsing a forwarded message."""
        raw_message = {
            "message_id": 12345,
            "from": {"id": 123, "first_name": "Test"},
            "text": "Forwarded content",
            "date": 1705320000,
            "forward_from_message_id": 99999,
        }

        result = await scraper.parse_message(raw_message)

        assert result["repost_of_id"] == "99999"

    def test_parse_entities_bold(self, scraper):
        """Test parsing bold text entity."""
        text = "Hello bold world"
        entities = [{"type": "bold", "offset": 6, "length": 4}]

        result = scraper._parse_entities(text, entities)

        assert "<b>bold</b>" in result

    def test_parse_entities_italic(self, scraper):
        """Test parsing italic text entity."""
        text = "Hello italic world"
        entities = [{"type": "italic", "offset": 6, "length": 6}]

        result = scraper._parse_entities(text, entities)

        assert "<i>italic</i>" in result

    def test_parse_entities_url(self, scraper):
        """Test parsing URL entity."""
        text = "Visit https://example.com today"
        entities = [{"type": "url", "offset": 6, "length": 19}]

        result = scraper._parse_entities(text, entities)

        assert '<a href="https://example.com">' in result

    def test_parse_entities_mention(self, scraper):
        """Test parsing mention entity."""
        text = "Hello @username!"
        entities = [{"type": "mention", "offset": 6, "length": 9}]

        result = scraper._parse_entities(text, entities)

        assert 'href="https://t.me/username"' in result

    def test_parse_entities_multiple(self, scraper):
        """Test parsing multiple entities."""
        text = "Hello bold and italic"
        entities = [
            {"type": "bold", "offset": 6, "length": 4},
            {"type": "italic", "offset": 15, "length": 6},
        ]

        result = scraper._parse_entities(text, entities)

        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result

    def test_parse_entities_empty(self, scraper):
        """Test parsing with no entities."""
        text = "Plain text"
        entities = []

        result = scraper._parse_entities(text, entities)

        assert result == text


class TestBaseSocialScraper:
    """Test cases for base scraper functionality."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock social session."""
        session = MagicMock(spec=SocialSession)
        session.id = 1
        session.session_key = "test:test:123"
        session.platform = Platform.TWITTER
        session.status = SessionStatus.ACTIVE
        session.message_count = 0
        return session

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock()

    def test_validate_message_valid(self, mock_session, mock_db):
        """Test message validation with valid data."""
        scraper = TwitterScraper(session=mock_session, db=mock_db, bearer_token="test")

        message = {
            "message_id": "123",
            "author_id": "456",
            "author_name": "Test",
            "content": "Hello",
            "posted_at": datetime.now(),
        }

        assert scraper.validate_message(message) is True

    def test_validate_message_missing_required(self, mock_session, mock_db):
        """Test message validation with missing required field."""
        scraper = TwitterScraper(session=mock_session, db=mock_db, bearer_token="test")

        message = {
            "message_id": "123",
            # Missing author_id
            "author_name": "Test",
            "content": "Hello",
            "posted_at": datetime.now(),
        }

        assert scraper.validate_message(message) is False

    def test_validate_message_no_content(self, mock_session, mock_db):
        """Test message validation with no content or media."""
        scraper = TwitterScraper(session=mock_session, db=mock_db, bearer_token="test")

        message = {
            "message_id": "123",
            "author_id": "456",
            "author_name": "Test",
            "content": "",
            "media_urls": [],
            "posted_at": datetime.now(),
        }

        assert scraper.validate_message(message) is False

    def test_validate_message_media_only(self, mock_session, mock_db):
        """Test message validation with media but no text."""
        scraper = TwitterScraper(session=mock_session, db=mock_db, bearer_token="test")

        message = {
            "message_id": "123",
            "author_id": "456",
            "author_name": "Test",
            "content": "",
            "media_urls": ["https://example.com/image.jpg"],
            "posted_at": datetime.now(),
        }

        assert scraper.validate_message(message) is True
