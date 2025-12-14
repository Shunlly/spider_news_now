"""
Tests for Proxies API endpoints.
"""

import pytest
from httpx import AsyncClient


class TestProxiesAPI:
    """Test cases for /api/v1/proxies endpoints."""

    @pytest.mark.asyncio
    async def test_list_proxies_empty(self, client: AsyncClient):
        """Test listing proxies when none exist."""
        response = await client.get("/api/v1/proxies")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_proxy(self, client: AsyncClient, sample_proxy):
        """Test creating a new proxy."""
        response = await client.post("/api/v1/proxies", json=sample_proxy)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "代理创建成功"
        assert data["proxy"]["name"] == sample_proxy["name"]
        assert data["proxy"]["host"] == sample_proxy["host"]
        assert data["proxy"]["port"] == sample_proxy["port"]
        assert data["proxy"]["protocol"] == sample_proxy["protocol"]

    @pytest.mark.asyncio
    async def test_create_proxy_socks5(self, client: AsyncClient):
        """Test creating a SOCKS5 proxy."""
        proxy = {
            "name": "SOCKS5 Proxy",
            "protocol": "socks5",
            "host": "socks.example.com",
            "port": 1080,
        }
        response = await client.post("/api/v1/proxies", json=proxy)
        assert response.status_code == 200
        data = response.json()
        assert data["proxy"]["protocol"] == "socks5"

    @pytest.mark.asyncio
    async def test_list_proxies_with_data(self, client: AsyncClient, sample_proxy):
        """Test listing proxies after creating one."""
        # Create proxy
        await client.post("/api/v1/proxies", json=sample_proxy)

        # List proxies
        response = await client.get("/api/v1/proxies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_list_proxies_filter_by_protocol(self, client: AsyncClient):
        """Test filtering proxies by protocol."""
        # Create HTTP proxy
        await client.post("/api/v1/proxies", json={
            "name": "HTTP Proxy",
            "protocol": "http",
            "host": "http.example.com",
            "port": 8080,
        })

        # Create SOCKS5 proxy
        await client.post("/api/v1/proxies", json={
            "name": "SOCKS5 Proxy",
            "protocol": "socks5",
            "host": "socks.example.com",
            "port": 1080,
        })

        # Filter by HTTP
        response = await client.get("/api/v1/proxies?protocol=http")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["protocol"] == "http"

    @pytest.mark.asyncio
    async def test_list_proxies_filter_by_enabled(self, client: AsyncClient, sample_proxy):
        """Test filtering proxies by enabled status."""
        # Create proxy (enabled by default)
        await client.post("/api/v1/proxies", json=sample_proxy)

        # Filter by enabled
        response = await client.get("/api/v1/proxies?enabled=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Filter by disabled
        response = await client.get("/api/v1/proxies?enabled=false")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_proxy(self, client: AsyncClient, sample_proxy):
        """Test getting a specific proxy."""
        # Create proxy
        create_response = await client.post("/api/v1/proxies", json=sample_proxy)
        proxy_id = create_response.json()["proxy_id"]

        # Get proxy
        response = await client.get(f"/api/v1/proxies/{proxy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == proxy_id
        assert data["name"] == sample_proxy["name"]

    @pytest.mark.asyncio
    async def test_get_proxy_not_found(self, client: AsyncClient):
        """Test getting a non-existent proxy."""
        response = await client.get("/api/v1/proxies/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_proxy(self, client: AsyncClient, sample_proxy):
        """Test updating a proxy."""
        # Create proxy
        create_response = await client.post("/api/v1/proxies", json=sample_proxy)
        proxy_id = create_response.json()["proxy_id"]

        # Update proxy
        update_data = {"name": "Updated Proxy", "port": 9090}
        response = await client.put(f"/api/v1/proxies/{proxy_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proxy"]["name"] == "Updated Proxy"
        assert data["proxy"]["port"] == 9090

    @pytest.mark.asyncio
    async def test_delete_proxy(self, client: AsyncClient, sample_proxy):
        """Test deleting a proxy."""
        # Create proxy
        create_response = await client.post("/api/v1/proxies", json=sample_proxy)
        proxy_id = create_response.json()["proxy_id"]

        # Delete proxy
        response = await client.delete(f"/api/v1/proxies/{proxy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deleted
        get_response = await client.get(f"/api/v1/proxies/{proxy_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_enable_proxy(self, client: AsyncClient, sample_proxy):
        """Test enabling a proxy."""
        # Create proxy
        create_response = await client.post("/api/v1/proxies", json=sample_proxy)
        proxy_id = create_response.json()["proxy_id"]

        # Enable proxy
        response = await client.post(f"/api/v1/proxies/{proxy_id}/enable")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proxy"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_disable_proxy(self, client: AsyncClient, sample_proxy):
        """Test disabling a proxy."""
        # Create proxy
        create_response = await client.post("/api/v1/proxies", json=sample_proxy)
        proxy_id = create_response.json()["proxy_id"]

        # Disable proxy
        response = await client.post(f"/api/v1/proxies/{proxy_id}/disable")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proxy"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_proxy_status_unknown_on_create(self, client: AsyncClient, sample_proxy):
        """Test that proxy status is unknown on creation."""
        response = await client.post("/api/v1/proxies", json=sample_proxy)
        assert response.status_code == 200
        data = response.json()
        assert data["proxy"]["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_proxy_statistics_initialized(self, client: AsyncClient, sample_proxy):
        """Test that proxy statistics are initialized correctly."""
        response = await client.post("/api/v1/proxies", json=sample_proxy)
        assert response.status_code == 200
        data = response.json()
        proxy = data["proxy"]
        assert proxy["request_count"] == 0
        assert proxy["success_count"] == 0
        assert proxy["failure_count"] == 0
        assert proxy["avg_response_time"] is None

    @pytest.mark.asyncio
    async def test_proxy_ordering_by_priority(self, client: AsyncClient):
        """Test that proxies are ordered by priority."""
        # Create proxies with different priorities
        await client.post("/api/v1/proxies", json={
            "name": "Low Priority",
            "protocol": "http",
            "host": "low.example.com",
            "port": 8080,
            "priority": 1,
        })

        await client.post("/api/v1/proxies", json={
            "name": "High Priority",
            "protocol": "http",
            "host": "high.example.com",
            "port": 8080,
            "priority": 10,
        })

        # List proxies (should be ordered by priority desc)
        response = await client.get("/api/v1/proxies")
        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["name"] == "High Priority"
        assert data["data"][1]["name"] == "Low Priority"
