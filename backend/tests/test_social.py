"""
Tests for Social API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestSocialSessionsAPI:
    """Test cases for /api/v1/social/sessions endpoints."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client: AsyncClient):
        """Test listing sessions when none exist."""
        response = await client.get("/api/v1/social/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient, sample_social_session):
        """Test creating a new social session."""
        response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["platform"] == sample_social_session["platform"]
        assert data["session"]["target_id"] == sample_social_session["target_id"]
        assert data["session"]["target_name"] == sample_social_session["target_name"]
        assert data["session"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_telegram_session(self, client: AsyncClient):
        """Test creating a Telegram session."""
        session = {
            "platform": "telegram",
            "target_type": "channel",
            "target_id": "-1001234567890",
            "target_name": "Test Channel",
            "description": "Test Telegram channel",
        }
        response = await client.post("/api/v1/social/sessions", json=session)
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["platform"] == "telegram"

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, client: AsyncClient, sample_social_session):
        """Test listing sessions after creating one."""
        # Create session
        await client.post("/api/v1/social/sessions", json=sample_social_session)

        # List sessions
        response = await client.get("/api/v1/social/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_platform(self, client: AsyncClient):
        """Test filtering sessions by platform."""
        # Create Twitter session
        await client.post("/api/v1/social/sessions", json={
            "platform": "twitter",
            "target_type": "user",
            "target_id": "123",
            "target_name": "Twitter User",
        })

        # Create Telegram session
        await client.post("/api/v1/social/sessions", json={
            "platform": "telegram",
            "target_type": "channel",
            "target_id": "-100123",
            "target_name": "Telegram Channel",
        })

        # Filter by Twitter
        response = await client.get("/api/v1/social/sessions?platform=twitter")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["platform"] == "twitter"

    @pytest.mark.asyncio
    async def test_list_sessions_filter_by_status(self, client: AsyncClient, sample_social_session):
        """Test filtering sessions by status."""
        # Create session
        await client.post("/api/v1/social/sessions", json=sample_social_session)

        # Filter by active status
        response = await client.get("/api/v1/social/sessions?status=active")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Filter by paused status
        response = await client.get("/api/v1/social/sessions?status=paused")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_session(self, client: AsyncClient, sample_social_session):
        """Test getting a specific session."""
        # Create session
        create_response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        session_id = create_response.json()["session"]["id"]

        # Get session
        response = await client.get(f"/api/v1/social/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient):
        """Test getting a non-existent session."""
        response = await client.get("/api/v1/social/sessions/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_session(self, client: AsyncClient, sample_social_session):
        """Test updating a session."""
        # Create session
        create_response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        session_id = create_response.json()["session"]["id"]

        # Update session
        update_data = {"target_name": "Updated Name", "description": "Updated description"}
        response = await client.put(f"/api/v1/social/sessions/{session_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["target_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient, sample_social_session):
        """Test deleting a session."""
        # Create session
        create_response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        session_id = create_response.json()["session"]["id"]

        # Delete session
        response = await client.delete(f"/api/v1/social/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        get_response = await client.get(f"/api/v1/social/sessions/{session_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_pause_session(self, client: AsyncClient, sample_social_session):
        """Test pausing a session."""
        # Create session
        create_response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        session_id = create_response.json()["session"]["id"]

        # Pause session
        response = await client.post(f"/api/v1/social/sessions/{session_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["status"] == "paused"

    @pytest.mark.asyncio
    async def test_resume_session(self, client: AsyncClient, sample_social_session):
        """Test resuming a paused session."""
        # Create session
        create_response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        session_id = create_response.json()["session"]["id"]

        # Pause session
        await client.post(f"/api/v1/social/sessions/{session_id}/pause")

        # Resume session
        response = await client.post(f"/api/v1/social/sessions/{session_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_session_key_generated(self, client: AsyncClient, sample_social_session):
        """Test that session_key is generated on creation."""
        response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        assert response.status_code == 200
        data = response.json()
        assert "session_key" in data["session"]
        assert data["session"]["session_key"] is not None

    @pytest.mark.asyncio
    async def test_session_statistics_initialized(self, client: AsyncClient, sample_social_session):
        """Test that session statistics are initialized correctly."""
        response = await client.post("/api/v1/social/sessions", json=sample_social_session)
        assert response.status_code == 200
        data = response.json()
        session = data["session"]
        assert session["message_count"] == 0
        assert session["last_message_at"] is None


class TestSocialStatisticsAPI:
    """Test cases for /api/v1/social/statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, client: AsyncClient):
        """Test getting statistics when no data exists."""
        response = await client.get("/api/v1/social/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 0
        assert data["total_messages"] == 0
        assert data["active_sessions"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, client: AsyncClient, sample_social_session):
        """Test getting statistics with data."""
        # Create session
        await client.post("/api/v1/social/sessions", json=sample_social_session)

        # Get statistics
        response = await client.get("/api/v1/social/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 1
        assert data["active_sessions"] == 1
