"""Integration tests for scheduler."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from app.models.news_source import NewsSource


@pytest.mark.integration
class TestSchedulerIntegration:
    """Integration tests for APScheduler scraper jobs."""

    @pytest.mark.asyncio
    async def test_register_scraper_jobs(self, db_session, test_user):
        """Test registering scraper jobs from database."""
        # Add test sources
        sources = [
            NewsSource(
                user_id=test_user.id,
                source_key="test1",
                display_name="Test Source 1",
                scraper_module="app.scrapers.sina_scraper",
                enabled=True,
                schedule_interval=1800,
            ),
            NewsSource(
                user_id=test_user.id,
                source_key="test2",
                display_name="Test Source 2",
                scraper_module="app.scrapers.qq_scraper",
                enabled=False,  # Disabled, should not be registered
                schedule_interval=1800,
            ),
        ]

        for source in sources:
            db_session.add(source)
        await db_session.commit()

        # Create async context manager mock for AsyncSessionLocal
        @asynccontextmanager
        async def mock_session_context():
            yield db_session

        # Register jobs with mocks
        with patch('app.tasks.scraper_tasks.AsyncSessionLocal', mock_session_context), \
             patch('app.tasks.scraper_tasks.get_scheduler') as mock_get_scheduler:
            mock_scheduler_instance = AsyncMock()
            mock_get_scheduler.return_value = mock_scheduler_instance

            from app.tasks.scraper_tasks import register_scraper_jobs
            await register_scraper_jobs()

            # Verify only enabled source was registered (add_schedule is APScheduler 4.0 API)
            assert mock_scheduler_instance.add_schedule.call_count == 1

    @pytest.mark.asyncio
    async def test_run_scraper_job_creates_run_record(self, db_session, test_user):
        """Test that scraper job creates ScraperRun record."""
        # Add test source
        source = NewsSource(
            user_id=test_user.id,
            source_key="sina",
            display_name="新浪新闻",
            scraper_module="app.scrapers.sina_scraper",
            enabled=True,
            schedule_interval=1800,
        )
        db_session.add(source)
        await db_session.commit()

        # Create async context manager mock for AsyncSessionLocal
        @asynccontextmanager
        async def mock_session_context():
            yield db_session

        # Mock the scraper service to avoid actual network calls
        with patch('app.tasks.scraper_tasks.AsyncSessionLocal', mock_session_context), \
             patch('app.services.scraper_service.ScraperService.run_scraper') as mock_run:
            # Mock returns a run_id
            mock_run.return_value = "mock-run-id-123"

            from app.tasks.scraper_tasks import run_scraper_job
            await run_scraper_job("sina")

            # Verify the scraper service was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][1] == "sina"  # source_key argument
