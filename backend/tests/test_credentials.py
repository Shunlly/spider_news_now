"""
Tests for Credentials API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestCredentialsAPI:
    """Test cases for /api/v1/credentials endpoints."""

    @pytest.mark.asyncio
    async def test_list_credentials_empty(self, client: AsyncClient):
        """Test listing credentials when none exist."""
        response = await client.get("/api/v1/credentials")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_credential(self, client: AsyncClient, sample_credential):
        """Test creating a new credential."""
        response = await client.post("/api/v1/credentials", json=sample_credential)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "凭证创建成功"
        assert data["credential"]["name"] == sample_credential["name"]
        assert data["credential"]["platform"] == sample_credential["platform"]

    @pytest.mark.asyncio
    async def test_create_credential_telegram(self, client: AsyncClient):
        """Test creating a Telegram credential."""
        credential = {
            "name": "Telegram Bot",
            "platform": "telegram",
            "credentials": {"bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"},
            "is_default": True,
        }
        response = await client.post("/api/v1/credentials", json=credential)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["credential"]["platform"] == "telegram"
        assert data["credential"]["is_default"] is True

    @pytest.mark.asyncio
    async def test_list_credentials_with_data(self, client: AsyncClient, sample_credential):
        """Test listing credentials after creating one."""
        # Create credential
        await client.post("/api/v1/credentials", json=sample_credential)

        # List credentials
        response = await client.get("/api/v1/credentials")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == sample_credential["name"]

    @pytest.mark.asyncio
    async def test_list_credentials_filter_by_platform(self, client: AsyncClient):
        """Test filtering credentials by platform."""
        # Create Twitter credential
        await client.post("/api/v1/credentials", json={
            "name": "Twitter Cred",
            "platform": "twitter",
            "credentials": {"bearer_token": "token1"},
        })

        # Create Telegram credential
        await client.post("/api/v1/credentials", json={
            "name": "Telegram Cred",
            "platform": "telegram",
            "credentials": {"bot_token": "token2"},
        })

        # Filter by Twitter
        response = await client.get("/api/v1/credentials?platform=twitter")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["platform"] == "twitter"

    @pytest.mark.asyncio
    async def test_get_credential(self, client: AsyncClient, sample_credential):
        """Test getting a specific credential."""
        # Create credential
        create_response = await client.post("/api/v1/credentials", json=sample_credential)
        credential_id = create_response.json()["credential_id"]

        # Get credential
        response = await client.get(f"/api/v1/credentials/{credential_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == credential_id
        assert data["name"] == sample_credential["name"]

    @pytest.mark.asyncio
    async def test_get_credential_not_found(self, client: AsyncClient):
        """Test getting a non-existent credential."""
        response = await client.get("/api/v1/credentials/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_credential(self, client: AsyncClient, sample_credential):
        """Test updating a credential."""
        # Create credential
        create_response = await client.post("/api/v1/credentials", json=sample_credential)
        credential_id = create_response.json()["credential_id"]

        # Update credential
        update_data = {"name": "Updated Name", "is_default": True}
        response = await client.put(f"/api/v1/credentials/{credential_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["credential"]["name"] == "Updated Name"
        assert data["credential"]["is_default"] is True

    @pytest.mark.asyncio
    async def test_delete_credential(self, client: AsyncClient, sample_credential):
        """Test deleting a credential."""
        # Create credential
        create_response = await client.post("/api/v1/credentials", json=sample_credential)
        credential_id = create_response.json()["credential_id"]

        # Delete credential
        response = await client.delete(f"/api/v1/credentials/{credential_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        get_response = await client.get(f"/api/v1/credentials/{credential_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_test_credential(self, client: AsyncClient, sample_credential):
        """Test the credential test endpoint."""
        # Create credential
        create_response = await client.post("/api/v1/credentials", json=sample_credential)
        credential_id = create_response.json()["credential_id"]

        # Test credential (will succeed because bearer_token is present)
        response = await client.post(f"/api/v1/credentials/{credential_id}/test")
        assert response.status_code == 200
        data = response.json()
        # Note: The test is a placeholder implementation
        assert "success" in data

    @pytest.mark.asyncio
    async def test_set_default_credential(self, client: AsyncClient):
        """Test setting a credential as default."""
        # Create two credentials
        cred1 = await client.post("/api/v1/credentials", json={
            "name": "Cred 1",
            "platform": "twitter",
            "credentials": {"bearer_token": "token1"},
            "is_default": True,
        })
        cred1_id = cred1.json()["credential_id"]

        cred2 = await client.post("/api/v1/credentials", json={
            "name": "Cred 2",
            "platform": "twitter",
            "credentials": {"bearer_token": "token2"},
            "is_default": False,
        })
        cred2_id = cred2.json()["credential_id"]

        # Set cred2 as default
        response = await client.post(f"/api/v1/credentials/{cred2_id}/set-default")
        assert response.status_code == 200
        assert response.json()["credential"]["is_default"] is True

        # Verify cred1 is no longer default
        cred1_response = await client.get(f"/api/v1/credentials/{cred1_id}")
        assert cred1_response.json()["is_default"] is False

    @pytest.mark.asyncio
    async def test_create_default_clears_other_defaults(self, client: AsyncClient):
        """Test that creating a default credential clears other defaults."""
        # Create first default credential
        await client.post("/api/v1/credentials", json={
            "name": "Cred 1",
            "platform": "twitter",
            "credentials": {"bearer_token": "token1"},
            "is_default": True,
        })

        # Create second default credential
        await client.post("/api/v1/credentials", json={
            "name": "Cred 2",
            "platform": "twitter",
            "credentials": {"bearer_token": "token2"},
            "is_default": True,
        })

        # List and verify only one is default
        response = await client.get("/api/v1/credentials?platform=twitter")
        data = response.json()
        defaults = [c for c in data["data"] if c["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["name"] == "Cred 2"
