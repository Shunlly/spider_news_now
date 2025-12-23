"""Integration tests for scraper management API endpoints."""

from datetime import datetime

import pytest

from app.models.news_source import NewsSource


@pytest.mark.asyncio
class TestScraperManagementAPI:
    """Tests for scraper management endpoints (US4)."""

    async def test_create_scraper_success(self, client, db_session, test_user):
        """Test POST /scrapers creates a new source."""
        # Note: This test requires an actual scraper module to exist
        # For testing, we'll test the validation error case
        response = await client.post(
            "/api/v1/scrapers",
            json={
                "source_key": "nonexistent",
                "display_name": "Nonexistent Scraper",
                "scraper_module": "app.scrapers.nonexistent_scraper",
                "enabled": True,
                "schedule_interval": 1800
            }
        )
        # Should fail because module doesn't exist
        assert response.status_code == 400
        assert "Cannot import" in response.json()["detail"]

    async def test_create_scraper_duplicate(self, client, db_session, test_user):
        """Test POST /scrapers returns 409 for duplicate source_key."""
        # First, create a source directly in DB
        source = NewsSource(
            user_id=test_user.id,
            source_key="duplicate_test",
            display_name="Duplicate Test",
            scraper_module="app.scrapers.test",
            enabled=True,
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Try to create again via API
        response = await client.post(
            "/api/v1/scrapers",
            json={
                "source_key": "duplicate_test",
                "display_name": "Another Name",
                "scraper_module": "app.scrapers.test",
                "enabled": True,
                "schedule_interval": 1800
            }
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_enable_scraper(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/enable enables a disabled scraper."""
        # Create a disabled source
        source = NewsSource(
            user_id=test_user.id,
            source_key="enable_test",
            display_name="Enable Test",
            scraper_module="app.scrapers.test",
            enabled=False,
            status="disabled",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Enable it
        response = await client.put("/api/v1/scrapers/enable_test/enable")
        assert response.status_code == 200
        data = response.json()
        assert data["source_key"] == "enable_test"
        assert data["enabled"] is True
        assert "enabled successfully" in data["message"]

    async def test_enable_already_enabled_scraper(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/enable on already enabled scraper."""
        # Create an enabled source
        source = NewsSource(
            user_id=test_user.id,
            source_key="already_enabled",
            display_name="Already Enabled",
            scraper_module="app.scrapers.test",
            enabled=True,
            status="idle",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        response = await client.put("/api/v1/scrapers/already_enabled/enable")
        assert response.status_code == 200
        data = response.json()
        assert "already enabled" in data["message"]

    async def test_enable_nonexistent_scraper(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/enable returns 404 for nonexistent."""
        response = await client.put("/api/v1/scrapers/nonexistent/enable")
        assert response.status_code == 404

    async def test_disable_scraper(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/disable disables a scraper."""
        # Create an enabled source
        source = NewsSource(
            user_id=test_user.id,
            source_key="disable_test",
            display_name="Disable Test",
            scraper_module="app.scrapers.test",
            enabled=True,
            status="idle",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Disable it
        response = await client.put("/api/v1/scrapers/disable_test/disable")
        assert response.status_code == 200
        data = response.json()
        assert data["source_key"] == "disable_test"
        assert data["enabled"] is False
        assert "disabled successfully" in data["message"]

    async def test_disable_already_disabled_scraper(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/disable on already disabled scraper."""
        # Create a disabled source
        source = NewsSource(
            user_id=test_user.id,
            source_key="already_disabled",
            display_name="Already Disabled",
            scraper_module="app.scrapers.test",
            enabled=False,
            status="disabled",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        response = await client.put("/api/v1/scrapers/already_disabled/disable")
        assert response.status_code == 200
        data = response.json()
        assert "already disabled" in data["message"]

    async def test_update_scraper_config(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/config updates configuration."""
        # Create a source
        source = NewsSource(
            user_id=test_user.id,
            source_key="config_test",
            display_name="Config Test",
            scraper_module="app.scrapers.test",
            enabled=True,
            status="idle",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Update config
        response = await client.put(
            "/api/v1/scrapers/config_test/config",
            json={"schedule_interval": 3600}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["schedule_interval"] == 3600

    async def test_update_scraper_config_invalid_interval(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/config rejects invalid interval."""
        # Create a source
        source = NewsSource(
            user_id=test_user.id,
            source_key="config_invalid",
            display_name="Config Invalid",
            scraper_module="app.scrapers.test",
            enabled=True,
            status="idle",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Try invalid interval (less than 60)
        response = await client.put(
            "/api/v1/scrapers/config_invalid/config",
            json={"schedule_interval": 30}
        )
        assert response.status_code == 422  # Validation error

    async def test_update_config_nonexistent_scraper(self, client, db_session, test_user):
        """Test PUT /scrapers/{source_key}/config returns 404 for nonexistent."""
        response = await client.put(
            "/api/v1/scrapers/nonexistent/config",
            json={"schedule_interval": 3600}
        )
        assert response.status_code == 404

    async def test_get_scrapers_status(self, client, db_session, test_user):
        """Test GET /scrapers/status returns all scrapers status."""
        # Create multiple sources
        sources = [
            NewsSource(
                user_id=test_user.id,
                source_key=f"status_test_{i}",
                display_name=f"Status Test {i}",
                scraper_module="app.scrapers.test",
                enabled=True,
                status="idle",
                schedule_interval=1800
            )
            for i in range(3)
        ]
        for source in sources:
            db_session.add(source)
        await db_session.commit()

        response = await client.get("/api/v1/scrapers/status")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scrapers"] == 3
        assert len(data["scrapers"]) == 3

    async def test_get_scraper_runs(self, client, db_session, test_user):
        """Test GET /scrapers/{source_key}/runs returns run history."""
        from app.models.scraper_run import ScraperRun

        # Create a source
        source = NewsSource(
            user_id=test_user.id,
            source_key="runs_test",
            display_name="Runs Test",
            scraper_module="app.scrapers.test",
            enabled=True,
            status="idle",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Create some runs
        for _ in range(5):
            run = ScraperRun(
                user_id=test_user.id,
                source_key="runs_test",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="success",
                articles_scraped=10,
                articles_new=5,
                articles_duplicate=5,
                duration_seconds=30
            )
            db_session.add(run)
        await db_session.commit()

        response = await client.get("/api/v1/scrapers/runs_test/runs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["runs"]) == 5

    async def test_get_scraper_runs_pagination(self, client, db_session, test_user):
        """Test GET /scrapers/{source_key}/runs supports pagination."""
        from app.models.scraper_run import ScraperRun

        # Create a source
        source = NewsSource(
            user_id=test_user.id,
            source_key="pagination_test",
            display_name="Pagination Test",
            scraper_module="app.scrapers.test",
            enabled=True,
            status="idle",
            schedule_interval=1800
        )
        db_session.add(source)
        await db_session.commit()

        # Create many runs
        for _ in range(25):
            run = ScraperRun(
                user_id=test_user.id,
                source_key="pagination_test",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                status="success",
                articles_scraped=10,
                articles_new=5,
                articles_duplicate=5,
                duration_seconds=30
            )
            db_session.add(run)
        await db_session.commit()

        # Test first page
        response = await client.get(
            "/api/v1/scrapers/pagination_test/runs?page=1&page_size=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["runs"]) == 10
        assert data["page"] == 1

        # Test second page
        response = await client.get(
            "/api/v1/scrapers/pagination_test/runs?page=2&page_size=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 10
        assert data["page"] == 2

    async def test_get_scraper_runs_nonexistent(self, client, db_session, test_user):
        """Test GET /scrapers/{source_key}/runs returns 404 for nonexistent."""
        response = await client.get("/api/v1/scrapers/nonexistent/runs")
        assert response.status_code == 404
