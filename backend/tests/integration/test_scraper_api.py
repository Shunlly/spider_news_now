"""Integration tests for scraper API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.news_source import NewsSource


@pytest.mark.integration
class TestScraperAPI:
    """Integration tests for scraper management API."""

    @pytest.mark.asyncio
    async def test_trigger_scraper_success(self, client: AsyncClient, db_session):
        """Test manually triggering a scraper."""
        # Create test source
        source = NewsSource(
            source_key="test_source",
            display_name="Test Source",
            scraper_module="app.scrapers.sina_scraper",
            enabled=True,
            status="idle",
        )
        db_session.add(source)
        await db_session.commit()

        # Trigger scraper
        response = await client.post("/api/v1/scrapers/test_source/trigger")

        assert response.status_code == 202
        data = response.json()
        assert data["source_key"] == "test_source"
        assert data["message"] == "Scraper triggered successfully"
        assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_trigger_nonexistent_scraper(self, client: AsyncClient, db_session):
        """Test triggering a non-existent scraper."""
        response = await client.post("/api/v1/scrapers/nonexistent/trigger")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_disabled_scraper(self, client: AsyncClient, db_session):
        """Test triggering a disabled scraper."""
        # Create disabled source
        source = NewsSource(
            source_key="disabled_source",
            display_name="Disabled Source",
            scraper_module="app.scrapers.sina_scraper",
            enabled=False,
            status="disabled",
        )
        db_session.add(source)
        await db_session.commit()

        response = await client.post("/api/v1/scrapers/disabled_source/trigger")

        assert response.status_code == 400
        assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_running_scraper(self, client: AsyncClient, db_session):
        """Test triggering a scraper that is already running."""
        # Create running source
        source = NewsSource(
            source_key="running_source",
            display_name="Running Source",
            scraper_module="app.scrapers.sina_scraper",
            enabled=True,
            status="running",
        )
        db_session.add(source)
        await db_session.commit()

        response = await client.post("/api/v1/scrapers/running_source/trigger")

        assert response.status_code == 409
        assert "already running" in response.json()["detail"].lower()
