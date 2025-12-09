"""Integration tests for scrapers."""

import pytest

from app.models.news_article import NewsArticle
from app.scrapers.sina_scraper import SinaScraper
from sqlalchemy import select


@pytest.mark.integration
class TestScraperIntegration:
    """Integration tests for scraper execution and database insertion."""

    @pytest.mark.asyncio
    async def test_sina_scraper_run_and_save(self, db_session):
        """Test running Sina scraper and saving articles to database."""
        # Create scraper
        scraper = SinaScraper()

        # Run scraper
        articles = await scraper.run()

        # Verify articles were scraped
        assert len(articles) > 0
        assert all(isinstance(a, dict) for a in articles)

        # Verify required fields
        for article in articles:
            assert "url" in article
            assert "url_hash" in article
            assert "title" in article
            assert "source_key" in article
            assert article["source_key"] == "sina"
            assert len(article["url_hash"]) == 64

        # Insert into database
        article_models = [NewsArticle(**article) for article in articles[:5]]  # Test with 5
        db_session.add_all(article_models)
        await db_session.commit()

        # Verify articles in database
        stmt = select(NewsArticle).where(NewsArticle.source_key == "sina")
        result = await db_session.execute(stmt)
        saved_articles = result.scalars().all()

        assert len(saved_articles) == 5
        assert all(a.source_key == "sina" for a in saved_articles)

    @pytest.mark.asyncio
    async def test_scraper_duplicate_detection(self, db_session):
        """Test that duplicate articles are not inserted."""
        scraper = SinaScraper()
        articles = await scraper.run()

        if len(articles) == 0:
            pytest.skip("No articles scraped")

        # Insert first article
        article_data = articles[0]
        article1 = NewsArticle(**article_data)
        db_session.add(article1)
        await db_session.commit()

        # Try to insert same article again (should be prevented by unique url_hash)
        article2 = NewsArticle(**article_data)
        db_session.add(article2)

        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await db_session.commit()
