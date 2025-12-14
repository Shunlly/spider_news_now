"""Contract tests for scraper output schemas."""

import pytest
from datetime import datetime
from typing import Dict, Any

from app.schemas.news import NewsArticleCreate


class TestScraperOutputContract:
    """
    Contract tests to verify scraper output matches NewsArticle schema.

    These tests ensure that all scrapers produce output compatible with
    the database schema, preventing runtime errors during article insertion.
    """

    @pytest.fixture
    def valid_scraper_output(self) -> Dict[str, Any]:
        """Valid scraper output matching contract."""
        return {
            "url": "https://news.sina.com.cn/example/article123",
            "url_hash": "a" * 64,  # 64-char SHA-256 hash
            "title": "测试新闻标题",
            "source_key": "sina",
            "category": "ent",
            "published_at": datetime.now(),
            "content_hash": None,
        }

    def test_valid_article_schema(self, valid_scraper_output: Dict[str, Any]):
        """Test that valid scraper output passes schema validation."""
        # Should not raise validation error
        article = NewsArticleCreate(**valid_scraper_output)

        assert str(article.url) == valid_scraper_output["url"]
        assert article.title == valid_scraper_output["title"]
        assert article.source_key == valid_scraper_output["source_key"]

    def test_url_hash_required(self, valid_scraper_output: Dict[str, Any]):
        """Test that url_hash is required."""
        invalid_output = valid_scraper_output.copy()
        del invalid_output["url_hash"]

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

    def test_url_hash_must_be_64_chars(self, valid_scraper_output: Dict[str, Any]):
        """Test that url_hash must be exactly 64 characters (SHA-256)."""
        # Too short
        invalid_output = valid_scraper_output.copy()
        invalid_output["url_hash"] = "abc123"

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

        # Too long
        invalid_output["url_hash"] = "a" * 100

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

    def test_title_required_and_non_empty(self, valid_scraper_output: Dict[str, Any]):
        """Test that title is required and cannot be empty."""
        # Missing title
        invalid_output = valid_scraper_output.copy()
        del invalid_output["title"]

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

        # Empty title
        invalid_output = valid_scraper_output.copy()
        invalid_output["title"] = ""

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

    def test_source_key_pattern_validation(self, valid_scraper_output: Dict[str, Any]):
        """Test that source_key must match pattern (lowercase alphanumeric + underscore)."""
        # Invalid: uppercase
        invalid_output = valid_scraper_output.copy()
        invalid_output["source_key"] = "Sina"

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

        # Invalid: special characters
        invalid_output["source_key"] = "sina-news"

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

        # Valid: lowercase with underscore
        invalid_output["source_key"] = "sina_news"
        article = NewsArticleCreate(**invalid_output)
        assert article.source_key == "sina_news"

    def test_category_optional(self, valid_scraper_output: Dict[str, Any]):
        """Test that category is optional."""
        valid_output = valid_scraper_output.copy()
        valid_output["category"] = None

        article = NewsArticleCreate(**valid_output)
        assert article.category is None

    def test_content_hash_optional(self, valid_scraper_output: Dict[str, Any]):
        """Test that content_hash is optional."""
        valid_output = valid_scraper_output.copy()
        valid_output["content_hash"] = None

        article = NewsArticleCreate(**valid_output)
        assert article.content_hash is None

    def test_url_must_be_valid_http(self, valid_scraper_output: Dict[str, Any]):
        """Test that URL must be valid HTTP/HTTPS."""
        # Invalid: not a URL
        invalid_output = valid_scraper_output.copy()
        invalid_output["url"] = "not-a-url"

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

        # Invalid: missing protocol
        invalid_output["url"] = "news.sina.com.cn/article"

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

    def test_published_at_datetime_type(self, valid_scraper_output: Dict[str, Any]):
        """Test that published_at must be a valid datetime."""
        # Note: Pydantic v2 auto-parses ISO date strings to datetime
        # So we test with invalid date format instead
        invalid_output = valid_scraper_output.copy()
        invalid_output["published_at"] = "invalid-date-format"

        with pytest.raises(ValueError):
            NewsArticleCreate(**invalid_output)

        # Valid: datetime object
        valid_output = valid_scraper_output.copy()
        valid_output["published_at"] = datetime(2025, 12, 8, 10, 30, 0)

        article = NewsArticleCreate(**valid_output)
        assert isinstance(article.published_at, datetime)

    def test_multiple_articles_batch(self, valid_scraper_output: Dict[str, Any]):
        """Test that multiple articles can be created (simulates batch insert)."""
        articles = []

        for i in range(10):
            output = valid_scraper_output.copy()
            output["url"] = f"https://news.sina.com.cn/article{i}"
            output["url_hash"] = f"{i:064d}"  # Different hash for each
            output["title"] = f"测试新闻标题 {i}"

            article = NewsArticleCreate(**output)
            articles.append(article)

        assert len(articles) == 10
        assert all(isinstance(a, NewsArticleCreate) for a in articles)
