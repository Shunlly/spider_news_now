"""
Integration tests for Search API endpoints.

Tests the full search workflow with mocked Meilisearch service.
Includes multi-tenant isolation tests (T182).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests for search functionality."""

    @pytest.fixture
    def mock_search_service(self):
        """Create a mock search service."""
        mock = MagicMock()
        mock.INDEX_NAME = "news_articles"
        return mock

    @pytest.mark.asyncio
    async def test_search_basic_query(self, client: AsyncClient, mock_search_service):
        """Test basic search with query."""
        mock_search_service.search = AsyncMock(return_value={
            "hits": [
                {
                    "id": 1,
                    "title": "Test Article",
                    "url": "https://example.com/article",
                    "source_key": "test_source",
                    "category": "tech",
                    "published_at": 1704067200,
                    "_formatted": {
                        "title": "<em>Test</em> Article",
                        "content": "This is <em>test</em> content"
                    }
                }
            ],
            "query": "test",
            "total_hits": 1,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 1,
            "processing_time_ms": 5,
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get("/api/v1/search?q=test")

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test"
            assert data["total_hits"] == 1
            assert len(data["hits"]) == 1
            assert data["hits"][0]["title"] == "Test Article"
            assert "<em>" in data["hits"][0]["title_highlighted"]

    @pytest.mark.asyncio
    async def test_search_with_filters(self, client: AsyncClient, mock_search_service):
        """Test search with source and category filters."""
        mock_search_service.search = AsyncMock(return_value={
            "hits": [],
            "query": "news",
            "total_hits": 0,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 0,
            "processing_time_ms": 3,
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get(
                "/api/v1/search?q=news&source_key=sina&category=tech"
            )

            assert response.status_code == 200
            mock_search_service.search.assert_called_once()
            call_args = mock_search_service.search.call_args
            assert call_args.kwargs["source_key"] == "sina"
            assert call_args.kwargs["category"] == "tech"

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, client: AsyncClient, mock_search_service):
        """Test search pagination."""
        mock_search_service.search = AsyncMock(return_value={
            "hits": [{"id": i, "title": f"Article {i}", "url": f"http://x/{i}", "source_key": "s"} for i in range(10)],
            "query": "article",
            "total_hits": 100,
            "page": 2,
            "hits_per_page": 10,
            "total_pages": 10,
            "processing_time_ms": 8,
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get("/api/v1/search?q=article&page=2&hits_per_page=10")

            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["hits_per_page"] == 10
            assert data["total_pages"] == 10
            assert data["total_hits"] == 100

    @pytest.mark.asyncio
    async def test_search_with_date_range(self, client: AsyncClient, mock_search_service):
        """Test search with date range filter."""
        mock_search_service.search = AsyncMock(return_value={
            "hits": [],
            "query": "test",
            "total_hits": 0,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 0,
            "processing_time_ms": 2,
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get(
                "/api/v1/search?q=test&start_date=2024-01-01T00:00:00&end_date=2024-12-31T23:59:59"
            )

            assert response.status_code == 200
            mock_search_service.search.assert_called_once()
            call_args = mock_search_service.search.call_args
            assert call_args.kwargs["start_date"] is not None
            assert call_args.kwargs["end_date"] is not None

    @pytest.mark.asyncio
    async def test_search_with_facets(self, client: AsyncClient, mock_search_service):
        """Test search with facet distribution."""
        mock_search_service.search_with_facets = AsyncMock(return_value=(
            {
                "hits": [
                    {"id": 1, "title": "News 1", "url": "http://x/1", "source_key": "sina"},
                    {"id": 2, "title": "News 2", "url": "http://x/2", "source_key": "qq"},
                ],
                "query": "breaking",
                "total_hits": 2,
                "page": 1,
                "hits_per_page": 20,
                "total_pages": 1,
                "processing_time_ms": 6,
            },
            {
                "source_key": {"sina": 50, "qq": 30, "twitter": 20},
                "category": {"tech": 60, "news": 40},
            }
        ))

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get("/api/v1/search/facets?q=breaking")

            assert response.status_code == 200
            data = response.json()
            assert "facets" in data
            assert len(data["facets"]["source_key"]) == 3
            assert len(data["facets"]["category"]) == 2

    @pytest.mark.asyncio
    async def test_search_index_stats_requires_admin(self, client: AsyncClient, mock_search_service):
        """Test getting index statistics - requires admin access."""
        # 索引统计是管理员操作
        response = await client.get("/api/v1/search/index/stats")
        # 普通用户应该被拒绝
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_search_empty_query_rejected(self, client: AsyncClient):
        """Test that empty query is rejected."""
        response = await client.get("/api/v1/search?q=")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_search_query_too_long_rejected(self, client: AsyncClient):
        """Test that query exceeding max length is rejected."""
        long_query = "a" * 201
        response = await client.get(f"/api/v1/search?q={long_query}")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_search_invalid_page_rejected(self, client: AsyncClient):
        """Test that invalid page number is rejected."""
        response = await client.get("/api/v1/search?q=test&page=0")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_search_service_error_handling(self, client: AsyncClient, mock_search_service):
        """Test error handling when search service fails."""
        mock_search_service.search = AsyncMock(side_effect=Exception("Meilisearch unavailable"))

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get("/api/v1/search?q=test")

            assert response.status_code == 500
            data = response.json()
            assert "搜索服务错误" in data["detail"]

    @pytest.mark.asyncio
    async def test_search_clear_index_requires_admin(self, client: AsyncClient, mock_search_service):
        """Test clearing search index - requires admin access."""
        # 清除索引是管理员操作
        response = await client.post("/api/v1/search/index/clear")
        # 普通用户应该被拒绝
        assert response.status_code == 403


@pytest.mark.integration
class TestSearchPerformance:
    """Performance-related integration tests for search."""

    @pytest.mark.asyncio
    async def test_search_response_time_within_sla(self, client: AsyncClient):
        """Test that search response includes processing time."""
        mock_service = MagicMock()
        mock_service.INDEX_NAME = "news_articles"
        mock_service.search = AsyncMock(return_value={
            "hits": [],
            "query": "test",
            "total_hits": 0,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 0,
            "processing_time_ms": 45,  # Under 500ms SLA
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_service):
            response = await client.get("/api/v1/search?q=test")

            assert response.status_code == 200
            data = response.json()
            assert "processing_time_ms" in data
            assert data["processing_time_ms"] < 500  # SLA requirement


@pytest.mark.integration
class TestSearchMultiTenant:
    """Multi-tenant isolation tests for search (T182)."""

    @pytest.fixture
    def mock_search_service(self):
        """Create a mock search service."""
        mock = MagicMock()
        mock.INDEX_NAME = "news_articles"
        return mock

    @pytest.mark.asyncio
    async def test_search_passes_user_filter_for_regular_user(
        self, client: AsyncClient, mock_search_service
    ):
        """Test that regular users get user_id filter applied."""
        mock_search_service.search = AsyncMock(return_value={
            "hits": [],
            "query": "test",
            "total_hits": 0,
            "page": 1,
            "hits_per_page": 20,
            "total_pages": 0,
            "processing_time_ms": 5,
        })

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get("/api/v1/search?q=test")

            assert response.status_code == 200
            mock_search_service.search.assert_called_once()
            call_kwargs = mock_search_service.search.call_args.kwargs

            # Regular users should have user_id filter applied
            assert "user_id" in call_kwargs
            assert "tenant_id" in call_kwargs

    @pytest.mark.asyncio
    async def test_search_with_facets_passes_tenant_filter(
        self, client: AsyncClient, mock_search_service
    ):
        """Test that faceted search also applies tenant filtering."""
        mock_search_service.search_with_facets = AsyncMock(return_value=(
            {
                "hits": [],
                "query": "test",
                "total_hits": 0,
                "page": 1,
                "hits_per_page": 20,
                "total_pages": 0,
                "processing_time_ms": 5,
            },
            {"source_key": {}, "category": {}}
        ))

        with patch("app.api.v1.endpoints.search.get_search_service", return_value=mock_search_service):
            response = await client.get("/api/v1/search/facets?q=test")

            assert response.status_code == 200
            mock_search_service.search_with_facets.assert_called_once()
            call_kwargs = mock_search_service.search_with_facets.call_args.kwargs

            # Tenant filtering should be applied
            assert "user_id" in call_kwargs
            assert "tenant_id" in call_kwargs

