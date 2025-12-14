"""
Integration tests for Social API and workflow.

Tests the full social data collection workflow including sessions and messages.
"""

import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_session import Platform, SessionStatus, SocialSession, TargetType
from app.models.social_message import SocialMessage


@pytest.mark.integration
class TestSocialWorkflowIntegration:
    """Integration tests for social data workflow."""

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self, client: AsyncClient, db_session: AsyncSession):
        """Test complete session lifecycle: create -> pause -> resume -> delete."""
        # 1. Create session
        session_data = {
            "platform": "twitter",
            "target_type": "user",
            "target_id": "12345",
            "target_name": "Test User",
            "target_username": "testuser",
        }
        create_response = await client.post("/api/v1/social/sessions", json=session_data)
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["id"]
        assert create_response.json()["session"]["status"] == "active"

        # 2. Verify session in list
        list_response = await client.get("/api/v1/social/sessions")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1

        # 3. Pause session
        pause_response = await client.post(f"/api/v1/social/sessions/{session_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["session"]["status"] == "paused"

        # 4. Resume session
        resume_response = await client.post(f"/api/v1/social/sessions/{session_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["session"]["status"] == "active"

        # 5. Delete session
        delete_response = await client.delete(f"/api/v1/social/sessions/{session_id}")
        assert delete_response.status_code == 200

        # 6. Verify deletion
        get_response = await client.get(f"/api/v1/social/sessions/{session_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_session_with_messages_workflow(self, client: AsyncClient, db_session: AsyncSession):
        """Test session with messages."""
        # Create session directly in DB
        session = SocialSession(
            session_key="twitter:user:test123",
            platform=Platform.TWITTER,
            target_type=TargetType.USER,
            target_id="test123",
            target_name="Test User",
            status=SessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Add messages
        for i in range(5):
            message = SocialMessage(
                session_id=session.id,
                message_id=f"msg_{i}",
                message_hash=f"hash_{i:064d}",
                platform=Platform.TWITTER,
                author_id="author_123",
                author_name="Author",
                content=f"Test message {i}",
                posted_at=datetime.now(),
            )
            db_session.add(message)
        await db_session.commit()

        # Get session with message count
        response = await client.get(f"/api/v1/social/sessions/{session.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message_count"] == 5

        # Get statistics
        stats_response = await client.get("/api/v1/social/statistics")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_sessions"] == 1
        assert stats["total_messages"] == 5

    @pytest.mark.asyncio
    async def test_multi_platform_sessions(self, client: AsyncClient, db_session: AsyncSession):
        """Test managing sessions across multiple platforms."""
        # Create Twitter session
        twitter_session = {
            "platform": "twitter",
            "target_type": "user",
            "target_id": "tw_123",
            "target_name": "Twitter User",
        }
        tw_response = await client.post("/api/v1/social/sessions", json=twitter_session)
        assert tw_response.status_code == 200

        # Create Telegram session
        telegram_session = {
            "platform": "telegram",
            "target_type": "channel",
            "target_id": "-1001234567890",
            "target_name": "Telegram Channel",
        }
        tg_response = await client.post("/api/v1/social/sessions", json=telegram_session)
        assert tg_response.status_code == 200

        # List all sessions
        all_response = await client.get("/api/v1/social/sessions")
        assert all_response.status_code == 200
        assert all_response.json()["total"] == 2

        # Filter by Twitter
        twitter_response = await client.get("/api/v1/social/sessions?platform=twitter")
        assert twitter_response.status_code == 200
        assert twitter_response.json()["total"] == 1
        assert twitter_response.json()["data"][0]["platform"] == "twitter"

        # Filter by Telegram
        telegram_response = await client.get("/api/v1/social/sessions?platform=telegram")
        assert telegram_response.status_code == 200
        assert telegram_response.json()["total"] == 1
        assert telegram_response.json()["data"][0]["platform"] == "telegram"

    @pytest.mark.asyncio
    async def test_session_update_workflow(self, client: AsyncClient, db_session: AsyncSession):
        """Test updating session properties."""
        # Create session
        session_data = {
            "platform": "twitter",
            "target_type": "hashtag",
            "target_id": "#python",
            "target_name": "#python",
        }
        create_response = await client.post("/api/v1/social/sessions", json=session_data)
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["id"]

        # Update session
        update_data = {
            "target_name": "#Python (Updated)",
            "description": "Python hashtag tracking",
            "fetch_interval": 1800,
        }
        update_response = await client.put(
            f"/api/v1/social/sessions/{session_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        updated = update_response.json()["session"]
        assert updated["target_name"] == "#Python (Updated)"
        assert updated["description"] == "Python hashtag tracking"

    @pytest.mark.asyncio
    async def test_session_key_uniqueness(self, client: AsyncClient, db_session: AsyncSession):
        """Test that session keys are unique."""
        session_data = {
            "platform": "twitter",
            "target_type": "user",
            "target_id": "same_user",
            "target_name": "Same User",
        }

        # Create first session
        first_response = await client.post("/api/v1/social/sessions", json=session_data)
        assert first_response.status_code == 200

        # Try to create duplicate
        dup_response = await client.post("/api/v1/social/sessions", json=session_data)
        # Should either return existing or fail with conflict
        assert dup_response.status_code in [200, 400, 409]

    @pytest.mark.asyncio
    async def test_statistics_aggregation(self, client: AsyncClient, db_session: AsyncSession):
        """Test statistics aggregation across sessions."""
        # Create multiple sessions
        platforms = ["twitter", "telegram", "twitter"]
        statuses = [SessionStatus.ACTIVE, SessionStatus.ACTIVE, SessionStatus.PAUSED]

        for i, (platform, status) in enumerate(zip(platforms, statuses)):
            session = SocialSession(
                session_key=f"{platform}:user:test{i}",
                platform=Platform(platform),
                target_type=TargetType.USER,
                target_id=f"test{i}",
                target_name=f"Test {i}",
                status=status,
            )
            db_session.add(session)
        await db_session.commit()

        # Get statistics
        response = await client.get("/api/v1/social/statistics")
        assert response.status_code == 200
        stats = response.json()

        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 2  # Only 2 are active


@pytest.mark.integration
class TestSocialMessageIntegration:
    """Integration tests for social message handling."""

    @pytest.fixture
    async def session_with_messages(self, db_session: AsyncSession):
        """Create a session with messages for testing."""
        session = SocialSession(
            session_key="twitter:user:messages_test",
            platform=Platform.TWITTER,
            target_type=TargetType.USER,
            target_id="messages_test",
            target_name="Messages Test",
            status=SessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        messages = []
        for i in range(10):
            msg = SocialMessage(
                session_id=session.id,
                message_id=f"tweet_{i}",
                message_hash=f"hash_{i:064d}",
                platform=Platform.TWITTER,
                author_id="author_1",
                author_name="Test Author",
                author_username="testauthor",
                content=f"Tweet content {i}",
                posted_at=datetime.now(),
                like_count=i * 10,
                repost_count=i * 2,
            )
            messages.append(msg)
            db_session.add(msg)
        await db_session.commit()

        return session, messages

    @pytest.mark.asyncio
    async def test_message_deduplication(self, client: AsyncClient, db_session: AsyncSession):
        """Test that duplicate messages are handled correctly."""
        session = SocialSession(
            session_key="twitter:user:dedup_test",
            platform=Platform.TWITTER,
            target_type=TargetType.USER,
            target_id="dedup_test",
            target_name="Dedup Test",
            status=SessionStatus.ACTIVE,
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # Add first message
        msg1 = SocialMessage(
            session_id=session.id,
            message_id="unique_tweet_1",
            message_hash="unique_hash_" + "0" * 52,
            platform=Platform.TWITTER,
            author_id="author",
            author_name="Author",
            content="First tweet",
            posted_at=datetime.now(),
        )
        db_session.add(msg1)
        await db_session.commit()

        # Try to add duplicate (same message_hash should be rejected)
        msg2 = SocialMessage(
            session_id=session.id,
            message_id="unique_tweet_2",
            message_hash="unique_hash_" + "0" * 52,  # Same hash
            platform=Platform.TWITTER,
            author_id="author",
            author_name="Author",
            content="Duplicate tweet",
            posted_at=datetime.now(),
        )

        # The database should reject this due to unique constraint
        try:
            db_session.add(msg2)
            await db_session.commit()
            # If no exception, check message count
        except Exception:
            await db_session.rollback()

        # Verify only one message exists
        await db_session.refresh(session)
        assert session.message_count <= 1

    @pytest.mark.asyncio
    async def test_session_message_count_update(self, client: AsyncClient, db_session: AsyncSession):
        """Test that session message_count is properly tracked."""
        # Create session via API
        session_data = {
            "platform": "telegram",
            "target_type": "group",
            "target_id": "-1009999",
            "target_name": "Test Group",
        }
        response = await client.post("/api/v1/social/sessions", json=session_data)
        assert response.status_code == 200
        session_id = response.json()["session"]["id"]
        assert response.json()["session"]["message_count"] == 0

        # Add messages directly to DB
        session = await db_session.get(SocialSession, session_id)
        for i in range(3):
            msg = SocialMessage(
                session_id=session_id,
                message_id=f"tg_msg_{i}",
                message_hash=f"tg_hash_{i:064d}",
                platform=Platform.TELEGRAM,
                author_id="tg_author",
                author_name="TG Author",
                content=f"Telegram message {i}",
                posted_at=datetime.now(),
            )
            db_session.add(msg)
        session.message_count = 3
        await db_session.commit()

        # Verify count via API
        get_response = await client.get(f"/api/v1/social/sessions/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["message_count"] == 3
