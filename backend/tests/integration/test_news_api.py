"""Integration tests for news API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource


@pytest.mark.integration
class TestNewsAPI:
    """Integration tests for news article API."""

    @pytest.mark.asyncio
    async def test_get_articles_empty(self, client: AsyncClient, db_session):
        """Test retrieving articles from empty database."""
        response = await client.get("/api/v1/news/articles")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["data"]) == 0

    @pytest.mark.asyncio
    async def test_get_articles_with_data(self, client: AsyncClient, db_session, sample_news_source, sample_news_article):
        """Test retrieving articles with data."""
        # Add source and articles
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        for i in range(3):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            article = NewsArticle(**article_data)
            db_session.add(article)
        await db_session.commit()

        response = await client.get("/api/v1/news/articles")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3

    @pytest.mark.asyncio
    async def test_get_articles_pagination(self, client: AsyncClient, db_session, sample_news_source, sample_news_article):
        """Test pagination."""
        # Add source and articles
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        for i in range(15):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            article = NewsArticle(**article_data)
            db_session.add(article)
        await db_session.commit()

        # Page 1
        response = await client.get("/api/v1/news/articles?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["total"] == 15
        assert data["total_pages"] == 2

        # Page 2
        response = await client.get("/api/v1/news/articles?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5

    @pytest.mark.asyncio
    async def test_get_article_by_id(self, client: AsyncClient, db_session, sample_news_source, sample_news_article):
        """Test retrieving single article."""
        # Add source and article
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        article = NewsArticle(**sample_news_article)
        db_session.add(article)
        await db_session.commit()
        await db_session.refresh(article)

        response = await client.get(f"/api/v1/news/articles/{article.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article.id
        assert data["title"] == article.title
        assert "url_hash" in data

    @pytest.mark.asyncio
    async def test_get_article_not_found(self, client: AsyncClient, db_session):
        """Test retrieving non-existent article."""
        response = await client.get("/api/v1/news/articles/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_articles_grouped(self, client: AsyncClient, db_session, sample_news_source, sample_news_article):
        """Test grouped article retrieval."""
        # Add source
        source = NewsSource(**sample_news_source)
        source.enabled = True
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

        response = await client.get("/api/v1/news/articles/grouped?limit_per_source=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["groups"]) == 1
        assert data["groups"][0]["source_key"] == "test_source"
        assert len(data["groups"][0]["articles"]) == 5

    @pytest.mark.asyncio
    async def test_get_sources(self, client: AsyncClient, db_session, sample_news_source):
        """Test retrieving news sources."""
        # Add sources
        source1 = NewsSource(**sample_news_source)
        db_session.add(source1)

        source2_data = sample_news_source.copy()
        source2_data["source_key"] = "other_source"
        source2_data["enabled"] = False
        source2 = NewsSource(**source2_data)
        db_session.add(source2)
        await db_session.commit()

        # Get all sources
        response = await client.get("/api/v1/news/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

        # Get enabled only
        response = await client.get("/api/v1/news/sources?enabled_only=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_statistics(self, client: AsyncClient, db_session, sample_news_source):
        """Test statistics endpoint."""
        # Add source
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        response = await client.get("/api/v1/news/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data
        assert "articles_today" in data
        assert "by_source" in data
        assert "by_category" in data
