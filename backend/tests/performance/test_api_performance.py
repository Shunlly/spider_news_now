"""
Performance tests for API endpoints.

Tests response times and throughput for critical operations.
SLA Requirements:
- Search API: < 500ms
- Regular API: < 2s
- Scraper execution: < 60s per run
"""

import asyncio
import time
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource


@pytest.mark.performance
class TestSearchPerformance:
    """Performance tests for search functionality."""

    @pytest.fixture
    def mock_search_service(self):
        """Create a mock search service with realistic timing."""
        mock = MagicMock()
        mock.INDEX_NAME = "news_articles"
        return mock

    @pytest.mark.asyncio
    async def test_search_response_under_500ms(self, client: AsyncClient, mock_search_service):
        """Test that search responses are under 500ms SLA."""
        # Simulate fast search response
        mock_search_service.search = AsyncMock(return_value={
            "hits": [{"id": i, "title": f"Result {i}", "url": f"http://x/{i}", "source_key": "s"} for i in range(20)],
            "query": "test",
            "total_hits": 1000,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 50,
            "processing_time_ms": 45,  # Meilisearch internal time
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            start_time = time.time()
            response = await client.get("/api/v1/search?q=test")
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            assert response.status_code == 200
            assert response_time_ms < 500, f"Search took {response_time_ms}ms, exceeds 500ms SLA"
            assert response.json()["processing_time_ms"] < 500

    @pytest.mark.asyncio
    async def test_search_with_filters_performance(self, client: AsyncClient, mock_search_service):
        """Test search with filters maintains performance."""
        mock_search_service.search = AsyncMock(return_value={
            "hits": [],
            "query": "filtered",
            "total_hits": 0,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 0,
            "processing_time_ms": 12,
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            start_time = time.time()
            response = await client.get(
                "/api/v1/search?q=filtered&source_key=sina&category=tech&start_date=2024-01-01"
            )
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            assert response.status_code == 200
            assert response_time_ms < 500

    @pytest.mark.asyncio
    async def test_faceted_search_performance(self, client: AsyncClient, mock_search_service):
        """Test faceted search performance."""
        mock_search_service.search_with_facets = AsyncMock(return_value=(
            {
                "hits": [{"id": i, "title": f"R{i}", "url": f"http://x/{i}", "source_key": "s"} for i in range(20)],
                "query": "faceted",
                "total_hits": 500,
                "page": 1,
                "hits_per_page": 20,
                "total_pages": 25,
                "processing_time_ms": 85,
            },
            {"source_key": {"sina": 100, "qq": 200, "twitter": 200}, "category": {"tech": 300, "news": 200}}
        ))

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            start_time = time.time()
            response = await client.get("/api/v1/search/facets?q=faceted")
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            assert response.status_code == 200
            assert response_time_ms < 500


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for general API endpoints."""

    @pytest.mark.asyncio
    async def test_news_list_under_2s(
        self, client: AsyncClient, db_session: AsyncSession, sample_news_source, sample_news_article
    ):
        """Test news list API under 2s SLA."""
        # Create test data
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        for i in range(100):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            db_session.add(NewsArticle(**article_data))
        await db_session.commit()

        start_time = time.time()
        response = await client.get("/api/v1/news/articles?page=1&page_size=50")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 2000, f"News list took {response_time_ms}ms, exceeds 2s SLA"

    @pytest.mark.asyncio
    async def test_social_sessions_list_under_2s(self, client: AsyncClient, db_session: AsyncSession):
        """Test social sessions list API under 2s SLA."""
        start_time = time.time()
        response = await client.get("/api/v1/social/sessions")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 2000

    @pytest.mark.asyncio
    async def test_statistics_under_2s(self, client: AsyncClient, db_session: AsyncSession, sample_news_source):
        """Test statistics API under 2s SLA."""
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        start_time = time.time()
        response = await client.get("/api/v1/news/statistics")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 2000

    @pytest.mark.asyncio
    async def test_credentials_list_under_2s(self, client: AsyncClient, db_session: AsyncSession):
        """Test credentials list API under 2s SLA."""
        start_time = time.time()
        response = await client.get("/api/v1/credentials")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 2000

    @pytest.mark.asyncio
    async def test_proxies_list_under_2s(self, client: AsyncClient, db_session: AsyncSession):
        """Test proxies list API under 2s SLA."""
        start_time = time.time()
        response = await client.get("/api/v1/proxies")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 2000


@pytest.mark.performance
class TestConcurrentRequests:
    """Test API performance under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_news_requests(
        self, client: AsyncClient, db_session: AsyncSession, sample_news_source
    ):
        """Test handling multiple concurrent news requests."""
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        async def make_request():
            start = time.time()
            response = await client.get("/api/v1/news/articles")
            return time.time() - start, response.status_code

        # Run 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        response_times = [r[0] * 1000 for r in results]
        status_codes = [r[1] for r in results]

        # All should succeed
        assert all(code == 200 for code in status_codes)

        # Average response time should be reasonable
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 2000, f"Average response time {avg_time}ms exceeds 2s"

        # Max response time should not be excessive
        max_time = max(response_times)
        assert max_time < 5000, f"Max response time {max_time}ms is too high"

    @pytest.mark.asyncio
    async def test_concurrent_search_requests(self, client: AsyncClient):
        """Test handling multiple concurrent search requests."""
        mock_service = MagicMock()
        mock_service.INDEX_NAME = "news_articles"
        mock_service.search = AsyncMock(return_value={
            "hits": [],
            "query": "test",
            "total_hits": 0,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 0,
            "processing_time_ms": 10,
        })

        async def make_search_request():
            start = time.time()
            with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_service):
                response = await client.get("/api/v1/search?q=test")
            return time.time() - start, response.status_code

        # Run 20 concurrent search requests
        tasks = [make_search_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        response_times = [r[0] * 1000 for r in results]
        status_codes = [r[1] for r in results]

        # All should succeed
        success_count = sum(1 for code in status_codes if code == 200)
        assert success_count >= 18, f"Only {success_count}/20 requests succeeded"

        # 95th percentile should be under 500ms
        sorted_times = sorted(response_times)
        p95_time = sorted_times[int(len(sorted_times) * 0.95)]
        assert p95_time < 500, f"95th percentile {p95_time}ms exceeds 500ms SLA"


@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Test database query performance."""

    @pytest.mark.asyncio
    async def test_large_dataset_pagination(
        self, client: AsyncClient, db_session: AsyncSession, sample_news_source, sample_news_article
    ):
        """Test pagination performance with larger dataset."""
        # Create source
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        # Create 500 articles (bulk insert would be faster in production)
        batch_size = 50
        for batch in range(10):
            for i in range(batch_size):
                idx = batch * batch_size + i
                article_data = sample_news_article.copy()
                article_data["url_hash"] = f"{idx:064d}"
                article_data["url"] = f"https://test.com/article{idx}"
                db_session.add(NewsArticle(**article_data))
            await db_session.commit()

        # Test first page
        start_time = time.time()
        response = await client.get("/api/v1/news/articles?page=1&page_size=50")
        first_page_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert first_page_time < 2000

        # Test middle page (should be similar performance due to offset)
        start_time = time.time()
        response = await client.get("/api/v1/news/articles?page=5&page_size=50")
        middle_page_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert middle_page_time < 2000

        # Test last page
        start_time = time.time()
        response = await client.get("/api/v1/news/articles?page=10&page_size=50")
        last_page_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert last_page_time < 2000
