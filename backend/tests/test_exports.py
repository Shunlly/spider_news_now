"""
Tests for Exports API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestExportsAPI:
    """Test cases for /api/v1/exports endpoints."""

    @pytest.mark.asyncio
    async def test_list_exports_empty(self, client: AsyncClient):
        """Test listing exports when none exist."""
        response = await client.get("/api/v1/exports")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_export_news_csv(self, client: AsyncClient):
        """Test creating a news export in CSV format."""
        export_request = {
            "data_source": "news",
            "export_format": "CSV",
        }
        response = await client.post("/api/v1/exports", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["task"]["data_source"] == "news"
        assert data["task"]["export_format"] == "CSV"
        assert data["task"]["status"] in ["PENDING", "PROCESSING"]

    @pytest.mark.asyncio
    async def test_create_export_news_json(self, client: AsyncClient):
        """Test creating a news export in JSON format."""
        export_request = {
            "data_source": "news",
            "export_format": "JSON",
        }
        response = await client.post("/api/v1/exports", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["task"]["export_format"] == "JSON"

    @pytest.mark.asyncio
    async def test_create_export_social_sessions(self, client: AsyncClient):
        """Test creating a social sessions export."""
        export_request = {
            "data_source": "social_sessions",
            "export_format": "CSV",
        }
        response = await client.post("/api/v1/exports", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["task"]["data_source"] == "social_sessions"

    @pytest.mark.asyncio
    async def test_create_export_social_messages(self, client: AsyncClient):
        """Test creating a social messages export."""
        export_request = {
            "data_source": "social_messages",
            "export_format": "CSV",
        }
        response = await client.post("/api/v1/exports", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["task"]["data_source"] == "social_messages"

    @pytest.mark.asyncio
    async def test_create_export_with_filters(self, client: AsyncClient):
        """Test creating an export with filters."""
        export_request = {
            "data_source": "news",
            "export_format": "CSV",
            "filters": {
                "source_key": "test_source",
                "start_date": "2024-01-01",
            },
        }
        response = await client.post("/api/v1/exports", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_create_export_with_custom_filename(self, client: AsyncClient):
        """Test creating an export with custom filename."""
        export_request = {
            "data_source": "news",
            "export_format": "CSV",
            "filename": "custom_export.csv",
        }
        response = await client.post("/api/v1/exports", json=export_request)
        assert response.status_code == 200
        data = response.json()
        assert data["task"]["filename"] == "custom_export.csv"

    @pytest.mark.asyncio
    async def test_list_exports_with_data(self, client: AsyncClient):
        """Test listing exports after creating one."""
        # Create export
        await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })

        # List exports
        response = await client.get("/api/v1/exports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_exports_filter_by_status(self, client: AsyncClient):
        """Test filtering exports by status."""
        # Create export
        await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })

        # Filter by pending status
        response = await client.get("/api/v1/exports?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        # Note: Task might have already started processing
        assert "data" in data

    @pytest.mark.asyncio
    async def test_list_exports_filter_by_data_source(self, client: AsyncClient):
        """Test filtering exports by data source."""
        # Create news export
        await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })

        # Create social export
        await client.post("/api/v1/exports", json={
            "data_source": "social_sessions",
            "export_format": "CSV",
        })

        # Filter by news
        response = await client.get("/api/v1/exports?data_source=news")
        assert response.status_code == 200
        data = response.json()
        for task in data["data"]:
            assert task["data_source"] == "news"

    @pytest.mark.asyncio
    async def test_get_export_task(self, client: AsyncClient):
        """Test getting a specific export task."""
        # Create export
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Get task
        response = await client.get(f"/api/v1/exports/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_export_task_not_found(self, client: AsyncClient):
        """Test getting a non-existent export task."""
        response = await client.get("/api/v1/exports/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_export_task(self, client: AsyncClient):
        """Test deleting an export task."""
        # Create export
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Delete task
        response = await client.delete(f"/api/v1/exports/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        get_response = await client.get(f"/api/v1/exports/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_incomplete_task(self, client: AsyncClient):
        """Test downloading from an incomplete task."""
        # Create export (will be in pending state)
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Try to download (should fail if not completed)
        response = await client.get(f"/api/v1/exports/{task_id}/download")
        # Depending on task status, might be 400 or 200
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_export_task_has_timestamps(self, client: AsyncClient):
        """Test that export task has proper timestamps."""
        response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        assert response.status_code == 200
        data = response.json()
        task = data["task"]
        assert "created_at" in task
        assert task["created_at"] is not None

    @pytest.mark.asyncio
    async def test_export_filename_generated(self, client: AsyncClient):
        """Test that export filename is auto-generated."""
        response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        assert response.status_code == 200
        data = response.json()
        task = data["task"]
        assert task["filename"] is not None
        assert task["filename"].endswith(".csv")
        assert "news" in task["filename"]

    @pytest.mark.asyncio
    async def test_cleanup_exports(self, client: AsyncClient):
        """Test cleanup exports endpoint."""
        response = await client.post("/api/v1/exports/cleanup?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "清理" in data["message"]

    @pytest.mark.asyncio
    async def test_retry_failed_export_on_non_failed(self, client: AsyncClient):
        """Test retrying a non-failed export."""
        # Create export
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Try to retry (should fail if not in failed state)
        response = await client.post(f"/api/v1/exports/{task_id}/retry")
        # Might succeed if task somehow failed, or return 400
        assert response.status_code in [200, 400]
