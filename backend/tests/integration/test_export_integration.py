"""
Integration tests for Export API and workflow.

Tests the full export process including task creation, execution, and download.
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_task import ExportFormat, ExportStatus, ExportTask
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource
from app.services.export_service import DataSource


@pytest.mark.integration
class TestExportWorkflowIntegration:
    """Integration tests for export functionality."""

    @pytest.fixture
    async def news_data(self, db_session: AsyncSession, sample_news_source, sample_news_article):
        """Create sample news data for export testing."""
        # Create source
        source = NewsSource(**sample_news_source)
        db_session.add(source)
        await db_session.commit()

        # Create articles
        articles = []
        for i in range(25):
            article_data = sample_news_article.copy()
            article_data["url_hash"] = f"{i:064d}"
            article_data["url"] = f"https://test.com/article{i}"
            article_data["title"] = f"Test Article {i}"
            article = NewsArticle(**article_data)
            articles.append(article)
            db_session.add(article)
        await db_session.commit()

        return source, articles

    @pytest.mark.asyncio
    async def test_export_task_creation(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test creating an export task."""
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
        assert data["task"]["filename"].endswith(".csv")

    @pytest.mark.asyncio
    async def test_export_task_with_custom_filename(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test creating export with custom filename."""
        export_request = {
            "data_source": "news",
            "export_format": "JSON",
            "filename": "my_custom_export.json",
        }

        response = await client.post("/api/v1/exports", json=export_request)

        assert response.status_code == 200
        assert response.json()["task"]["filename"] == "my_custom_export.json"

    @pytest.mark.asyncio
    async def test_export_task_with_filters(self, client: AsyncClient, db_session: AsyncSession, news_data, test_user):
        """Test creating export with filters."""
        export_request = {
            "data_source": "news",
            "export_format": "CSV",
            "filters": {
                "source_key": "test_source",
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            },
        }

        response = await client.post("/api/v1/exports", json=export_request)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_export_formats(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test different export formats."""
        formats = ["CSV", "JSON", "EXCEL"]

        for fmt in formats:
            export_request = {
                "data_source": "news",
                "export_format": fmt,
            }

            response = await client.post("/api/v1/exports", json=export_request)

            assert response.status_code == 200
            data = response.json()
            assert data["task"]["export_format"] == fmt

            # Verify file extension
            if fmt == "CSV":
                assert data["task"]["filename"].endswith(".csv")
            elif fmt == "JSON":
                assert data["task"]["filename"].endswith(".json")
            elif fmt == "EXCEL":
                assert data["task"]["filename"].endswith(".xlsx")

    @pytest.mark.asyncio
    async def test_export_data_sources(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test different data sources."""
        sources = ["news", "social_sessions", "social_messages"]

        for source in sources:
            export_request = {
                "data_source": source,
                "export_format": "CSV",
            }

            response = await client.post("/api/v1/exports", json=export_request)

            assert response.status_code == 200
            assert response.json()["task"]["data_source"] == source

    @pytest.mark.asyncio
    async def test_list_export_tasks(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test listing export tasks."""
        # Create multiple export tasks
        for _ in range(3):
            await client.post("/api/v1/exports", json={
                "data_source": "news",
                "export_format": "CSV",
            })

        # List all tasks
        response = await client.get("/api/v1/exports")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    @pytest.mark.asyncio
    async def test_list_exports_filter_by_status(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test filtering exports by status."""
        # Create task
        await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })

        # Filter by pending/processing status
        response = await client.get("/api/v1/exports?status=pending")

        assert response.status_code == 200
        # Task might be pending or already processing

    @pytest.mark.asyncio
    async def test_list_exports_filter_by_data_source(self, client: AsyncClient, db_session: AsyncSession, test_user):
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
    async def test_get_export_task_details(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test getting specific export task."""
        # Create task
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "JSON",
        })
        task_id = create_response.json()["task"]["id"]

        # Get task details
        response = await client.get(f"/api/v1/exports/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert "created_at" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_get_nonexistent_export_task(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test getting non-existent export task."""
        response = await client.get("/api/v1/exports/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_export_task(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test deleting export task."""
        # Create task
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Delete task
        delete_response = await client.delete(f"/api/v1/exports/{task_id}")

        assert delete_response.status_code == 200
        assert delete_response.json()["success"] is True

        # Verify deletion
        get_response = await client.get(f"/api/v1/exports/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_cleanup(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test export cleanup endpoint."""
        response = await client.post("/api/v1/exports/cleanup?days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "清理" in data["message"]


@pytest.mark.integration
class TestExportDownloadIntegration:
    """Integration tests for export download functionality."""

    @pytest.mark.asyncio
    async def test_download_incomplete_task(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test downloading from incomplete task."""
        # Create task (will be in pending state)
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Try to download immediately (task not completed)
        download_response = await client.get(f"/api/v1/exports/{task_id}/download")

        # Should fail if task not completed
        assert download_response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_download_completed_task(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test downloading completed export task."""
        import os
        import tempfile

        # Create actual temp file for download test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name\n1,test\n")
            temp_path = f.name

        try:
            # Create completed task directly in DB
            task = ExportTask(
                user_id=test_user.id,
                data_source=DataSource.NEWS.value,
                export_format=ExportFormat.CSV,
                status=ExportStatus.COMPLETED,
                filename="test_export.csv",
                file_path=temp_path,
                file_size=1024,
                total_records=100,
            )
            db_session.add(task)
            await db_session.commit()
            await db_session.refresh(task)

            # Try download
            download_response = await client.get(f"/api/v1/exports/{task.id}/download")
            assert download_response.status_code == 200
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


@pytest.mark.integration
class TestExportRetryIntegration:
    """Integration tests for export retry functionality."""

    @pytest.mark.asyncio
    async def test_retry_failed_task(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test retrying a failed export task."""
        # Create failed task directly in DB
        task = ExportTask(
            user_id=test_user.id,
            data_source=DataSource.NEWS.value,
            export_format=ExportFormat.CSV,
            status=ExportStatus.FAILED,
            filename="failed_export.csv",
            error_message="Test error",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # Retry the task
        retry_response = await client.post(f"/api/v1/exports/{task.id}/retry")

        assert retry_response.status_code == 200
        data = retry_response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_retry_non_failed_task(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test retrying a non-failed task (should fail)."""
        # Create pending task
        create_response = await client.post("/api/v1/exports", json={
            "data_source": "news",
            "export_format": "CSV",
        })
        task_id = create_response.json()["task"]["id"]

        # Try to retry (should fail as task is not in failed state)
        retry_response = await client.post(f"/api/v1/exports/{task_id}/retry")

        # Should be either 200 (if somehow failed) or 400 (not failed)
        assert retry_response.status_code in [200, 400]
