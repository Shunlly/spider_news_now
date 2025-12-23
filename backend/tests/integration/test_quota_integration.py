"""
配额服务集成测试 - Quota Service Integration Tests
T121-T123: Quota Integration Tests

测试场景：
1. 配额创建和获取
2. 配额消耗和检查
3. 并发槽位管理
4. 配额 API 端点
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quota import Quota, QuotaTier
from app.models.user import User
from app.services.quota_service import QuotaService


class TestQuotaServiceIntegration:
    """配额服务集成测试"""

    @pytest_asyncio.fixture
    async def quota_service(self) -> QuotaService:
        """创建配额服务实例"""
        return QuotaService()

    @pytest.mark.asyncio
    async def test_get_or_create_quota_new_user(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试为新用户创建配额"""
        quota = await quota_service.get_or_create_quota(
            db_session, user_id=test_user.id, tier=QuotaTier.FREE
        )

        assert quota is not None
        assert quota.user_id == test_user.id
        assert quota.tier == QuotaTier.FREE.value
        assert quota.daily_limit == 100
        assert quota.daily_used == 0
        assert quota.concurrent_limit == 1
        assert quota.concurrent_used == 0

    @pytest.mark.asyncio
    async def test_get_or_create_quota_existing_user(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试获取已存在的配额"""
        # 创建配额
        quota1 = await quota_service.get_or_create_quota(
            db_session, user_id=test_user.id, tier=QuotaTier.FREE
        )

        # 再次获取应该返回相同的配额
        quota2 = await quota_service.get_or_create_quota(
            db_session, user_id=test_user.id, tier=QuotaTier.BASIC  # 等级参数会被忽略
        )

        assert quota1.id == quota2.id
        assert quota2.tier == QuotaTier.FREE.value  # 保持原等级

    @pytest.mark.asyncio
    async def test_check_daily_quota_available(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试检查每日配额 - 配额足够"""
        await quota_service.get_or_create_quota(db_session, test_user.id)

        has_quota, msg, remaining = await quota_service.check_daily_quota(
            db_session, test_user.id, amount=10
        )

        assert has_quota is True
        assert remaining == 100  # Free tier default

    @pytest.mark.asyncio
    async def test_check_daily_quota_exhausted(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试检查每日配额 - 配额不足"""
        quota = await quota_service.get_or_create_quota(db_session, test_user.id)
        quota.daily_used = 95
        await db_session.commit()

        has_quota, msg, remaining = await quota_service.check_daily_quota(
            db_session, test_user.id, amount=10
        )

        assert has_quota is False
        assert "用尽" in msg
        assert remaining == 5

    @pytest.mark.asyncio
    async def test_consume_daily_quota_success(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试消耗每日配额 - 成功"""
        await quota_service.get_or_create_quota(db_session, test_user.id)

        success, msg = await quota_service.consume_daily_quota(
            db_session, test_user.id, amount=25
        )

        assert success is True
        assert msg == ""

        # 验证消耗
        info = await quota_service.get_quota_info(db_session, test_user.id)
        assert info["daily_used"] == 25
        assert info["daily_remaining"] == 75

    @pytest.mark.asyncio
    async def test_consume_daily_quota_failure(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试消耗每日配额 - 配额不足"""
        quota = await quota_service.get_or_create_quota(db_session, test_user.id)
        quota.daily_used = 95
        await db_session.commit()

        success, msg = await quota_service.consume_daily_quota(
            db_session, test_user.id, amount=10
        )

        assert success is False
        assert "不足" in msg

    @pytest.mark.asyncio
    async def test_acquire_concurrent_slot_success(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试获取并发槽位 - 成功"""
        await quota_service.get_or_create_quota(db_session, test_user.id)

        success, msg = await quota_service.acquire_concurrent_slot(
            db_session, test_user.id
        )

        assert success is True

        info = await quota_service.get_quota_info(db_session, test_user.id)
        assert info["concurrent_used"] == 1

    @pytest.mark.asyncio
    async def test_acquire_concurrent_slot_at_limit(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试获取并发槽位 - 已达上限"""
        quota = await quota_service.get_or_create_quota(db_session, test_user.id)
        quota.concurrent_used = 1  # Free tier 只有 1 个并发
        await db_session.commit()

        success, msg = await quota_service.acquire_concurrent_slot(
            db_session, test_user.id
        )

        assert success is False
        assert "上限" in msg

    @pytest.mark.asyncio
    async def test_release_concurrent_slot(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试释放并发槽位"""
        quota = await quota_service.get_or_create_quota(db_session, test_user.id)
        quota.concurrent_used = 1
        await db_session.commit()

        await quota_service.release_concurrent_slot(db_session, test_user.id)

        info = await quota_service.get_quota_info(db_session, test_user.id)
        assert info["concurrent_used"] == 0

    @pytest.mark.asyncio
    async def test_get_quota_info(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试获取配额信息"""
        await quota_service.get_or_create_quota(db_session, test_user.id)

        info = await quota_service.get_quota_info(db_session, test_user.id)

        assert info["tier"] == QuotaTier.FREE.value
        assert info["daily_limit"] == 100
        assert info["daily_used"] == 0
        assert info["daily_remaining"] == 100
        assert info["concurrent_limit"] == 1
        assert info["concurrent_used"] == 0
        assert info["concurrent_remaining"] == 1
        assert info["warning"] is False

    @pytest.mark.asyncio
    async def test_update_tier(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试更新配额等级"""
        await quota_service.get_or_create_quota(db_session, test_user.id)

        quota = await quota_service.update_tier(
            db_session, test_user.id, QuotaTier.PRO
        )

        assert quota.tier == QuotaTier.PRO.value
        assert quota.daily_limit == 10000
        assert quota.concurrent_limit == 10

    @pytest.mark.asyncio
    async def test_warning_threshold(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试配额警告阈值"""
        quota = await quota_service.get_or_create_quota(db_session, test_user.id)
        quota.daily_used = 91  # < 10% remaining
        await db_session.commit()

        info = await quota_service.get_quota_info(db_session, test_user.id)
        assert info["warning"] is True


class TestQuotaApiEndpoint:
    """配额 API 端点测试"""

    @pytest.mark.asyncio
    async def test_get_quota_endpoint(self, client: AsyncClient, db_session: AsyncSession):
        """测试 GET /api/v1/quota 端点"""
        response = await client.get("/api/v1/quota")

        assert response.status_code == 200
        data = response.json()

        assert "tier" in data
        assert "daily_limit" in data
        assert "daily_used" in data
        assert "daily_remaining" in data
        assert "concurrent_limit" in data
        assert "concurrent_used" in data
        assert "concurrent_remaining" in data
        assert "warning" in data

    @pytest.mark.asyncio
    async def test_get_quota_endpoint_default_values(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """测试 GET /api/v1/quota 端点 - 默认值"""
        response = await client.get("/api/v1/quota")

        assert response.status_code == 200
        data = response.json()

        # 默认为 free tier
        assert data["tier"] == "free"
        assert data["daily_limit"] == 100
        assert data["concurrent_limit"] == 1


class TestQuotaTierLimits:
    """配额等级限制测试"""

    @pytest_asyncio.fixture
    async def quota_service(self) -> QuotaService:
        return QuotaService()

    @pytest.mark.asyncio
    async def test_free_tier_limits(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试 Free 等级限制"""
        quota = await quota_service.get_or_create_quota(
            db_session, test_user.id, QuotaTier.FREE
        )

        assert quota.daily_limit == 100
        assert quota.concurrent_limit == 1

    @pytest.mark.asyncio
    async def test_basic_tier_limits(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试 Basic 等级限制"""
        quota = await quota_service.get_or_create_quota(
            db_session, test_user.id, QuotaTier.BASIC
        )
        quota.update_tier(QuotaTier.BASIC)
        await db_session.commit()

        assert quota.daily_limit == 1000
        assert quota.concurrent_limit == 3

    @pytest.mark.asyncio
    async def test_pro_tier_limits(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试 Pro 等级限制"""
        quota = await quota_service.get_or_create_quota(
            db_session, test_user.id, QuotaTier.PRO
        )
        quota.update_tier(QuotaTier.PRO)
        await db_session.commit()

        assert quota.daily_limit == 10000
        assert quota.concurrent_limit == 10

    @pytest.mark.asyncio
    async def test_tier_upgrade_preserves_usage(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试等级升级保留使用量"""
        quota = await quota_service.get_or_create_quota(
            db_session, test_user.id, QuotaTier.FREE
        )
        quota.daily_used = 50
        await db_session.commit()

        # 升级到 Pro
        await quota_service.update_tier(db_session, test_user.id, QuotaTier.PRO)

        info = await quota_service.get_quota_info(db_session, test_user.id)
        assert info["daily_used"] == 50  # 使用量保留
        assert info["daily_limit"] == 10000  # 限额更新
        assert info["daily_remaining"] == 9950


class TestConcurrentQuotaManagement:
    """并发配额管理测试"""

    @pytest_asyncio.fixture
    async def quota_service(self) -> QuotaService:
        return QuotaService()

    @pytest.mark.asyncio
    async def test_multiple_acquire_release(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试多次获取和释放并发槽位"""
        # 升级到 Basic tier (3 并发)
        await quota_service.get_or_create_quota(db_session, test_user.id)
        await quota_service.update_tier(db_session, test_user.id, QuotaTier.BASIC)

        # 获取 3 个槽位
        for _ in range(3):
            success, _ = await quota_service.acquire_concurrent_slot(
                db_session, test_user.id
            )
            assert success is True

        # 第 4 个应该失败
        success, msg = await quota_service.acquire_concurrent_slot(
            db_session, test_user.id
        )
        assert success is False
        assert "上限" in msg

        # 释放 1 个
        await quota_service.release_concurrent_slot(db_session, test_user.id)

        # 再次获取应该成功
        success, _ = await quota_service.acquire_concurrent_slot(
            db_session, test_user.id
        )
        assert success is True

    @pytest.mark.asyncio
    async def test_release_at_zero(
        self, db_session: AsyncSession, test_user: User, quota_service: QuotaService
    ):
        """测试在 0 时释放不会变成负数"""
        await quota_service.get_or_create_quota(db_session, test_user.id)

        # 释放 (当前为 0)
        await quota_service.release_concurrent_slot(db_session, test_user.id)

        info = await quota_service.get_quota_info(db_session, test_user.id)
        assert info["concurrent_used"] == 0  # 不会变成负数
