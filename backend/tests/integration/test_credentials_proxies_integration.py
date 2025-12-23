"""
Integration tests for Credentials and Proxies API.

Tests the full credential and proxy management workflow.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
class TestCredentialsWorkflowIntegration:
    """Integration tests for credential management."""

    @pytest.mark.asyncio
    async def test_full_credential_lifecycle(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test complete credential lifecycle: create -> update -> set default -> delete."""
        # 1. Create credential
        credential_data = {
            "name": "Test Twitter Credential",
            "platform": "twitter",
            "credentials": {
                "bearer_token": "test_bearer_token_12345"
            },
        }
        create_response = await client.post("/api/v1/credentials", json=credential_data)
        assert create_response.status_code == 200
        cred_id = create_response.json()["credential"]["id"]

        # 2. Update credential
        update_data = {
            "name": "Updated Twitter Credential",
        }
        update_response = await client.put(f"/api/v1/credentials/{cred_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["credential"]["name"] == "Updated Twitter Credential"

        # 3. Set as default
        default_response = await client.post(f"/api/v1/credentials/{cred_id}/set-default")
        assert default_response.status_code == 200
        assert default_response.json()["credential"]["is_default"] is True

        # 4. Verify in list
        list_response = await client.get("/api/v1/credentials?platform=twitter")
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1

        # 5. Delete credential
        delete_response = await client.delete(f"/api/v1/credentials/{cred_id}")
        assert delete_response.status_code == 200

        # 6. Verify deletion
        get_response = await client.get(f"/api/v1/credentials/{cred_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_multi_platform_credentials(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test managing credentials across multiple platforms."""
        # Create Twitter credential
        twitter_cred = {
            "name": "Twitter API",
            "platform": "twitter",
            "credentials": {"bearer_token": "tw_token"},
        }
        tw_response = await client.post("/api/v1/credentials", json=twitter_cred)
        assert tw_response.status_code == 200

        # Create Telegram credential
        telegram_cred = {
            "name": "Telegram Bot",
            "platform": "telegram",
            "credentials": {"bot_token": "123456:ABC-DEF"},
        }
        tg_response = await client.post("/api/v1/credentials", json=telegram_cred)
        assert tg_response.status_code == 200

        # List all
        all_response = await client.get("/api/v1/credentials")
        assert all_response.status_code == 200
        assert all_response.json()["total"] == 2

        # Filter by platform
        twitter_only = await client.get("/api/v1/credentials?platform=twitter")
        assert twitter_only.json()["total"] == 1
        assert twitter_only.json()["data"][0]["platform"] == "twitter"

    @pytest.mark.asyncio
    async def test_default_credential_switching(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test that setting new default unsets previous default."""
        # Create first credential as default
        cred1 = {
            "name": "First Credential",
            "platform": "twitter",
            "credentials": {"bearer_token": "token1"},
            "is_default": True,
        }
        resp1 = await client.post("/api/v1/credentials", json=cred1)
        assert resp1.status_code == 200
        cred1_id = resp1.json()["credential"]["id"]

        # Create second credential
        cred2 = {
            "name": "Second Credential",
            "platform": "twitter",
            "credentials": {"bearer_token": "token2"},
        }
        resp2 = await client.post("/api/v1/credentials", json=cred2)
        assert resp2.status_code == 200
        cred2_id = resp2.json()["credential"]["id"]

        # Set second as default
        await client.post(f"/api/v1/credentials/{cred2_id}/set-default")

        # Verify first is no longer default
        get_resp1 = await client.get(f"/api/v1/credentials/{cred1_id}")
        assert get_resp1.json()["is_default"] is False

        # Verify second is default
        get_resp2 = await client.get(f"/api/v1/credentials/{cred2_id}")
        assert get_resp2.json()["is_default"] is True


@pytest.mark.integration
class TestProxiesWorkflowIntegration:
    """Integration tests for proxy management."""

    @pytest.mark.asyncio
    async def test_full_proxy_lifecycle(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test complete proxy lifecycle: create -> update -> disable -> enable -> delete."""
        # 1. Create proxy
        proxy_data = {
            "name": "Test HTTP Proxy",
            "protocol": "http",
            "host": "proxy.example.com",
            "port": 8080,
        }
        create_response = await client.post("/api/v1/proxies", json=proxy_data)
        assert create_response.status_code == 200
        proxy_id = create_response.json()["proxy_id"]

        # 2. Update proxy
        update_data = {
            "name": "Updated HTTP Proxy",
            "port": 8888,
        }
        update_response = await client.put(f"/api/v1/proxies/{proxy_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["proxy"]["port"] == 8888

        # 3. Disable proxy
        disable_response = await client.post(f"/api/v1/proxies/{proxy_id}/disable")
        assert disable_response.status_code == 200
        assert disable_response.json()["proxy"]["enabled"] is False

        # 4. Enable proxy
        enable_response = await client.post(f"/api/v1/proxies/{proxy_id}/enable")
        assert enable_response.status_code == 200
        assert enable_response.json()["proxy"]["enabled"] is True

        # 5. Delete proxy
        delete_response = await client.delete(f"/api/v1/proxies/{proxy_id}")
        assert delete_response.status_code == 200

        # 6. Verify deletion
        get_response = await client.get(f"/api/v1/proxies/{proxy_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_multi_protocol_proxies(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test managing proxies with different protocols."""
        protocols = ["http", "https", "socks5"]

        created_ids = []
        for protocol in protocols:
            proxy_data = {
                "name": f"{protocol.upper()} Proxy",
                "protocol": protocol,
                "host": f"{protocol}.proxy.com",
                "port": 8080 if protocol != "socks5" else 1080,
            }
            response = await client.post("/api/v1/proxies", json=proxy_data)
            assert response.status_code == 200
            created_ids.append(response.json()["proxy_id"])

        # List all
        all_response = await client.get("/api/v1/proxies")
        assert all_response.status_code == 200
        assert all_response.json()["total"] == 3

        # Filter by protocol
        http_only = await client.get("/api/v1/proxies?protocol=http")
        assert http_only.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_proxy_priority_ordering(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test that proxies are ordered by priority."""
        # Create low priority proxy
        low_priority = {
            "name": "Low Priority",
            "protocol": "http",
            "host": "low.proxy.com",
            "port": 8080,
            "priority": 1,
        }
        await client.post("/api/v1/proxies", json=low_priority)

        # Create high priority proxy
        high_priority = {
            "name": "High Priority",
            "protocol": "http",
            "host": "high.proxy.com",
            "port": 8080,
            "priority": 10,
        }
        await client.post("/api/v1/proxies", json=high_priority)

        # List proxies (should be ordered by priority desc)
        response = await client.get("/api/v1/proxies")
        assert response.status_code == 200
        data = response.json()["data"]

        # High priority should come first
        assert data[0]["name"] == "High Priority"
        assert data[1]["name"] == "Low Priority"

    @pytest.mark.asyncio
    async def test_proxy_with_authentication(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test proxy with username/password authentication."""
        proxy_data = {
            "name": "Authenticated Proxy",
            "protocol": "http",
            "host": "auth.proxy.com",
            "port": 8080,
            "username": "proxyuser",
            "password": "proxypass",
        }
        response = await client.post("/api/v1/proxies", json=proxy_data)

        assert response.status_code == 200
        proxy = response.json()["proxy"]
        assert proxy["username"] == "proxyuser"
        # Password should not be returned in response for security
        # or should be masked

    @pytest.mark.asyncio
    async def test_enabled_disabled_filtering(self, client: AsyncClient, db_session: AsyncSession, test_user):
        """Test filtering proxies by enabled status."""
        # Create enabled proxy
        enabled_proxy = {
            "name": "Enabled Proxy",
            "protocol": "http",
            "host": "enabled.proxy.com",
            "port": 8080,
        }
        await client.post("/api/v1/proxies", json=enabled_proxy)

        # Create and disable another proxy
        disabled_proxy = {
            "name": "Disabled Proxy",
            "protocol": "http",
            "host": "disabled.proxy.com",
            "port": 8080,
        }
        resp = await client.post("/api/v1/proxies", json=disabled_proxy)
        proxy_id = resp.json()["proxy_id"]
        await client.post(f"/api/v1/proxies/{proxy_id}/disable")

        # Filter enabled
        enabled_response = await client.get("/api/v1/proxies?enabled=true")
        assert enabled_response.status_code == 200
        for proxy in enabled_response.json()["data"]:
            assert proxy["enabled"] is True

        # Filter disabled
        disabled_response = await client.get("/api/v1/proxies?enabled=false")
        assert disabled_response.status_code == 200
        for proxy in disabled_response.json()["data"]:
            assert proxy["enabled"] is False
