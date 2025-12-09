"""Unit tests for duplicate detection service."""

import pytest

from app.services.duplicate_service import DuplicateService


class TestDuplicateService:
    """Test suite for DuplicateService."""

    def test_compute_url_hash_consistent(self):
        """Test that URL hashing is consistent."""
        url = "https://news.sina.com.cn/article/123"

        hash1 = DuplicateService.compute_url_hash(url)
        hash2 = DuplicateService.compute_url_hash(url)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 = 64 hex chars

    def test_compute_url_hash_normalizes_trailing_slash(self):
        """Test that trailing slashes are normalized."""
        url1 = "https://news.sina.com.cn/article/123"
        url2 = "https://news.sina.com.cn/article/123/"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)

        assert hash1 == hash2

    def test_compute_url_hash_removes_fragments(self):
        """Test that URL fragments are removed."""
        url1 = "https://news.sina.com.cn/article/123"
        url2 = "https://news.sina.com.cn/article/123#section1"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)

        assert hash1 == hash2

    def test_compute_url_hash_different_urls(self):
        """Test that different URLs produce different hashes."""
        url1 = "https://news.sina.com.cn/article/123"
        url2 = "https://news.sina.com.cn/article/456"

        hash1 = DuplicateService.compute_url_hash(url1)
        hash2 = DuplicateService.compute_url_hash(url2)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_get_existing_url_hashes_empty_set(self, db_session):
        """Test with empty hash set."""
        existing = await DuplicateService.get_existing_url_hashes(db_session, set())

        assert existing == set()

    @pytest.mark.asyncio
    async def test_filter_duplicates_all_new(self, db_session):
        """Test filtering when all articles are new."""
        articles = [
            {
                "url": "https://test.com/1",
                "url_hash": "a" * 64,
                "title": "Article 1",
                "source_key": "test",
                "category": "test",
                "published_at": "2025-12-08T10:00:00",
            },
            {
                "url": "https://test.com/2",
                "url_hash": "b" * 64,
                "title": "Article 2",
                "source_key": "test",
                "category": "test",
                "published_at": "2025-12-08T10:00:00",
            },
        ]

        new, duplicates = await DuplicateService.filter_duplicates(db_session, articles)

        assert len(new) == 2
        assert len(duplicates) == 0

    @pytest.mark.asyncio
    async def test_filter_duplicates_empty_list(self, db_session):
        """Test filtering empty article list."""
        new, duplicates = await DuplicateService.filter_duplicates(db_session, [])

        assert new == []
        assert duplicates == []
