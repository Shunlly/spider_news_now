"""Unit tests for news service."""

from datetime import datetime, timedelta

import pytest

from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource
from app.services.news_service import NewsService


@pytest.mark.asyncio
class TestNewsService:
    """Test suite for NewsService."""

    async def test_get_articles_empty_database(self, db_session):
        """Test retrieving articles from empty database."""
        articles, total = await NewsService.get_articles(db_session)

        assert articles == []
        assert total == 0

    async def test_get_articles_with_data(self, db_session, sample_news_source, sample_news_article):
        """Test retrieving articles with data."""
        # Add source
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        # Add articles
        for i in range(5):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            article = NewsArticle(**article_data)
            db_session.add(article)
        await db_session.commit()

        articles, total = await NewsService.get_articles(db_session, page_size=10)

        assert len(articles) == 5
        assert total == 5

    async def test_get_articles_pagination(self, db_session, sample_news_source, sample_news_article):
        """Test pagination."""
        # Add source
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        # Add 15 articles
        for i in range(15):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            article = NewsArticle(**article_data)
            db_session.add(article)
        await db_session.commit()

        # Page 1
        articles_p1, total = await NewsService.get_articles(db_session, page=1, page_size=10)
        assert len(articles_p1) == 10
        assert total == 15

        # Page 2
        articles_p2, total = await NewsService.get_articles(db_session, page=2, page_size=10)
        assert len(articles_p2) == 5
        assert total == 15

    async def test_get_articles_filter_by_source(self, db_session, sample_news_source, sample_news_article):
        """Test filtering by source."""
        # Add sources
        source1 = NewsSource(**sample_news_source)
        db_session.add(source1)

        source2_data = sample_news_source.copy()
        source2_data["source_key"] = "other_source"
        source2 = NewsSource(**source2_data)
        db_session.add(source2)
        await db_session.commit()

        # Add articles from both sources
        article1 = sample_news_article.copy()
        article1["url_hash"] = "a" * 64
        db_session.add(NewsArticle(**article1))

        article2 = sample_news_article.copy()
        article2["source_key"] = "other_source"
        article2["url_hash"] = "b" * 64
        article2["url"] = "https://other.com/article"
        db_session.add(NewsArticle(**article2))
        await db_session.commit()

        # Filter by first source
        articles, total = await NewsService.get_articles(db_session, source="test_source")
        assert len(articles) == 1
        assert total == 1
        assert articles[0].source_key == "test_source"

    async def test_get_articles_grouped(self, db_session, sample_news_source, sample_news_article):
        """Test grouped article retrieval."""
        # Add source
        source = NewsSource(**sample_news_source)
        source.enabled = True
        db_session.add(source)
        await db_session.commit()

        # Add recent articles
        for i in range(3):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            article_data["published_at"] = datetime.now() - timedelta(hours=1)
            article = NewsArticle(**article_data)
            db_session.add(article)
        await db_session.commit()

        groups = await NewsService.get_articles_grouped(db_session, limit_per_source=10)

        assert len(groups) == 1
        assert groups[0]["source_key"] == "test_source"
        assert len(groups[0]["articles"]) == 3

    async def test_get_article_by_id(self, db_session, sample_news_source, sample_news_article):
        """Test retrieving single article by ID."""
        # Add source and article
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        article = NewsArticle(**sample_news_article)
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)

        # Retrieve by ID
        retrieved = await NewsService.get_article_by_id(db_session, article.id)

        assert retrieved is not None
        assert retrieved.id == article.id
        assert retrieved.title == article.title

    async def test_get_article_by_id_not_found(self, db_session):
        """Test retrieving non-existent article."""
        retrieved = await NewsService.get_article_by_id(db_session, 99999)

        assert retrieved is None

    async def test_get_statistics(self, db_session, sample_news_source):
        """Test statistics retrieval."""
        # Add source
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        stats = await NewsService.get_statistics(db_session)

        assert "total_articles" in stats
        assert "articles_today" in stats
        assert "by_source" in stats
        assert "by_category" in stats
        assert stats["total_articles"] == 0  # No articles yet
