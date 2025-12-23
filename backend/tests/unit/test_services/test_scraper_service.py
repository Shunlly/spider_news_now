"""Unit tests for scraper orchestration service."""

import pytest

from app.models.news_source import NewsSource
from app.services.scraper_service import ScraperService


class TestScraperService:
    """Test suite for ScraperService."""

    @pytest.mark.asyncio
    async def test_load_scraper_success(self):
        """Test successful scraper loading."""
        scraper = await ScraperService.load_scraper("sina", "app.scrapers.sina_scraper")

        assert scraper is not None
        assert scraper.source_key == "sina"
        assert scraper.display_name == "新浪新闻"

    @pytest.mark.asyncio
    async def test_load_scraper_invalid_module(self):
        """Test loading non-existent scraper module."""
        with pytest.raises(ImportError):
            await ScraperService.load_scraper("invalid", "app.scrapers.invalid_scraper")

    @pytest.mark.asyncio
    async def test_get_scraper_status_empty_database(self, db_session):
        """Test status retrieval with no sources."""
        status = await ScraperService.get_scraper_status(db_session)

        assert status["total_scrapers"] == 0
        assert status["enabled"] == 0
        assert status["running"] == 0
        assert status["failed"] == 0

    @pytest.mark.asyncio
    async def test_get_scraper_status_with_sources(self, db_session, test_user):
        """Test status retrieval with multiple sources."""
        # Add test sources
        sources = [
            NewsSource(
                user_id=test_user.id,
                source_key="test1",
                display_name="Test 1",
                scraper_module="test",
                enabled=True,
                status="idle",
            ),
            NewsSource(
                user_id=test_user.id,
                source_key="test2",
                display_name="Test 2",
                scraper_module="test",
                enabled=True,
                status="running",
            ),
            NewsSource(
                user_id=test_user.id,
                source_key="test3",
                display_name="Test 3",
                scraper_module="test",
                enabled=False,
                status="failed",
            ),
        ]

        for source in sources:
            db_session.add(source)
        await db_session.commit()

        status = await ScraperService.get_scraper_status(db_session)

        assert status["total_scrapers"] == 3
        assert status["enabled"] == 2
        assert status["running"] == 1
        assert status["failed"] == 1
