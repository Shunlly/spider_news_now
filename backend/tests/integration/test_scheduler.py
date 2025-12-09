"""Integration tests for scheduler."""

import pytest
from unittest.mock import AsyncMock, patch

from app.tasks.scraper_tasks import run_scraper_job, register_scraper_jobs
from app.models.news_source import NewsSource
from app.models.scraper_run import ScraperRun
from sqlalchemy import select


@pytest.mark.integration
class TestSchedulerIntegration:
    """Integration tests for APScheduler scraper jobs."""

    @pytest.mark.asyncio
    async def test_register_scraper_jobs(self, db_session):
        """Test registering scraper jobs from database."""
        # Add test sources
        sources = [
            NewsSource(
                source_key="test1",
                display_name="Test Source 1",
                scraper_module="app.scrapers.sina_scraper",
                enabled=True,
                schedule_interval=1800,
            ),
            NewsSource(
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

        # Register jobs
        with patch('app.tasks.scraper_tasks.get_scheduler') as mock_scheduler:
            mock_scheduler_instance = AsyncMock()
            mock_scheduler_instance.get_job.return_value = None
            mock_scheduler.return_value = mock_scheduler_instance

            await register_scraper_jobs()

            # Verify only enabled source was registered
            assert mock_scheduler_instance.add_job.call_count == 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_run_scraper_job_creates_run_record(self, db_session):
        """Test that scraper job creates ScraperRun record."""
        # Add test source
        source = NewsSource(
            source_key="sina",
            display_name="新浪新闻",
            scraper_module="app.scrapers.sina_scraper",
            enabled=True,
            schedule_interval=1800,
        )
        db_session.add(source)
        await db_session.commit()

        # Run scraper job (this will actually scrape - mark as slow test)
        await run_scraper_job("sina")

        # Verify ScraperRun was created
        stmt = select(ScraperRun).where(ScraperRun.source_key == "sina")
        result = await db_session.execute(stmt)
        runs = result.scalars().all()

        assert len(runs) > 0
        run = runs[-1]  # Get latest run
        assert run.status in ["success", "failed", "timeout"]
        assert run.completed_at is not None
        assert run.duration_seconds is not None
