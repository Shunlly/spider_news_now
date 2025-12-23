"""Unit tests for audit service."""

import pytest

from app.models.audit import AuditAction, AuditLog


class TestAuditLogModel:
    """Test suite for AuditLog model."""

    def test_create_audit_log(self):
        """Test creating audit log entry."""
        log = AuditLog(
            user_id="test-user",
            action=AuditAction.LOGIN.value,
            resource_type="user",
            ip_address="127.0.0.1",
        )

        assert log.user_id == "test-user"
        assert log.action == AuditAction.LOGIN.value
        assert log.resource_type == "user"
        assert log.ip_address == "127.0.0.1"

    def test_audit_action_values(self):
        """Test audit action enum values."""
        assert AuditAction.LOGIN.value == "login"
        assert AuditAction.LOGOUT.value == "logout"
        assert AuditAction.CREATE.value == "create"
        assert AuditAction.UPDATE.value == "update"
        assert AuditAction.DELETE.value == "delete"
        assert AuditAction.TASK_RUN.value == "task_run"
        assert AuditAction.EXPORT.value == "export"
        assert AuditAction.LOGIN_FAILED.value == "login_failed"


class TestAuditServiceIntegration:
    """Integration tests for AuditService (requires database)."""

    @pytest.mark.asyncio
    async def test_log_action(self, db_session):
        """Test logging an action."""
        from app.services.audit_service import AuditService

        service = AuditService()
        log = await service.log(
            db=db_session,
            action=AuditAction.CREATE,
            resource_type="news_source",
            ip_address="192.168.1.1",
            user_id=None,  # No foreign key constraint issue
            resource_id="source-123",
            details={"source_key": "sina"},
        )

        assert log is not None
        assert log.action == AuditAction.CREATE.value
        assert log.resource_type == "news_source"

    @pytest.mark.asyncio
    async def test_log_login(self, db_session):
        """Test logging a login action."""
        from app.services.audit_service import AuditService

        service = AuditService()
        log = await service.log_login(
            db=db_session,
            user_id=None,  # No foreign key constraint issue
            user_email="test@example.com",
            ip_address="10.0.0.1",
            success=True,
        )

        assert log is not None
        assert log.action == AuditAction.LOGIN.value
        assert log.resource_type == "auth"

    @pytest.mark.asyncio
    async def test_log_failed_login(self, db_session):
        """Test logging a failed login action."""
        from app.services.audit_service import AuditService

        service = AuditService()
        log = await service.log_login(
            db=db_session,
            user_id=None,
            user_email="unknown@example.com",
            ip_address="10.0.0.1",
            success=False,
            error_message="Invalid password",
        )

        assert log is not None
        assert log.action == AuditAction.LOGIN_FAILED.value

    @pytest.mark.asyncio
    async def test_get_failed_login_attempts(self, db_session):
        """Test getting failed login attempts count."""
        from app.services.audit_service import AuditService

        service = AuditService()

        # Log some failed login attempts
        for _ in range(3):
            await service.log_login(
                db=db_session,
                user_id=None,
                user_email="attacker@example.com",
                ip_address="192.168.1.100",
                success=False,
            )

        count = await service.get_failed_login_attempts(
            db=db_session,
            ip_address="192.168.1.100",
            hours=1,
        )

        assert count == 3
