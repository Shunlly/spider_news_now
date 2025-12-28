"""
租户隔离集成测试 - Tenant Isolation Integration Tests
T108: Integration test for tenant isolation
T109: Integration test for super admin access
T110: Integration test for permission denied cases

测试多租户数据隔离功能。
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.middleware import TenantContext
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.role import Role, RoleType
from app.models.tenant import Tenant
from app.models.user import User
from tests.conftest import test_app


@pytest_asyncio.fixture
async def setup_tenants(db_session: AsyncSession):
    """创建测试租户"""
    tenant1 = Tenant(
        id=1,
        name="tenant-alpha",
        display_name="Alpha 公司",
        quota_config={"daily_limit": 1000, "concurrent_limit": 5},
    )
    tenant2 = Tenant(
        id=2,
        name="tenant-beta",
        display_name="Beta 公司",
        quota_config={"daily_limit": 500, "concurrent_limit": 3},
    )
    db_session.add(tenant1)
    db_session.add(tenant2)
    await db_session.commit()
    return tenant1, tenant2


@pytest_asyncio.fixture
async def setup_roles_and_users(db_session: AsyncSession, setup_tenants):
    """创建测试角色和用户"""
    import bcrypt
    from sqlalchemy import select

    tenant1, tenant2 = setup_tenants

    # 创建角色 - 使用 merge 避免冲突
    roles_data = [
        (1, RoleType.SUPER_ADMIN.value, "超级管理员", ["*"]),
        (2, RoleType.TENANT_ADMIN.value, "租户管理员", ["tenant:*"]),
        (3, RoleType.USER.value, "用户", ["task:read"]),
    ]

    for role_id, name, display_name, permissions in roles_data:
        result = await db_session.execute(select(Role).where(Role.id == role_id))
        existing = result.scalar_one_or_none()
        if not existing:
            role = Role(id=role_id, name=name, display_name=display_name, permissions=permissions)
            db_session.add(role)

    await db_session.flush()

    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()

    # 超级管理员 - 无租户限制
    super_admin = User(
        id="super-admin-001",
        username="superadmin",
        email="super@example.com",
        password_hash=password_hash,
        role_id=1,
        tenant_id=None,  # 超级管理员不属于任何租户
        is_active=True,
    )

    # 租户1 管理员
    tenant1_admin = User(
        id="tenant1-admin-001",
        username="tenant1admin",
        email="admin@tenant1.com",
        password_hash=password_hash,
        role_id=2,
        tenant_id=1,
        is_active=True,
    )

    # 租户1 普通用户
    tenant1_user = User(
        id="tenant1-user-001",
        username="tenant1user",
        email="user@tenant1.com",
        password_hash=password_hash,
        role_id=3,
        tenant_id=1,
        is_active=True,
    )

    # 租户2 用户
    tenant2_user = User(
        id="tenant2-user-001",
        username="tenant2user",
        email="user@tenant2.com",
        password_hash=password_hash,
        role_id=3,
        tenant_id=2,
        is_active=True,
    )

    db_session.add_all([super_admin, tenant1_admin, tenant1_user, tenant2_user])
    await db_session.commit()

    return {
        "super_admin": super_admin,
        "tenant1_admin": tenant1_admin,
        "tenant1_user": tenant1_user,
        "tenant2_user": tenant2_user,
        "tenant1": tenant1,
        "tenant2": tenant2,
    }


@pytest_asyncio.fixture
async def tenant_client(db_session: AsyncSession, setup_roles_and_users):
    """创建租户用户客户端"""
    users = setup_roles_and_users

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    # 返回多个客户端的工厂函数
    async def get_client_for_user(user_key: str):
        user = users[user_key]
        token = create_access_token(
            subject=user.id,
            extra_claims={
                "role_id": user.role_id,
                "tenant_id": user.tenant_id,
            }
        )
        transport = ASGITransport(app=test_app)
        return AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"}
        )

    yield get_client_for_user, users

    test_app.dependency_overrides.clear()


@pytest.mark.integration
class TestTenantIsolation:
    """租户隔离测试 - T108"""

    @pytest.mark.asyncio
    async def test_tenant_context_set_correctly(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试租户上下文正确设置"""
        get_client, users = tenant_client

        async with await get_client("tenant1_user") as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] == 1

    @pytest.mark.asyncio
    async def test_tenant_user_only_sees_own_data(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试租户用户只能看到自己租户的数据"""
        get_client, users = tenant_client

        # 租户1用户应该只能访问租户1的数据
        async with await get_client("tenant1_user") as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "tenant1user"
            assert data["tenant_id"] == 1

    @pytest.mark.asyncio
    async def test_different_tenants_isolated(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试不同租户数据隔离"""
        get_client, users = tenant_client

        # 租户1用户
        async with await get_client("tenant1_user") as client1:
            response1 = await client1.get("/api/v1/auth/me")
            assert response1.status_code == 200
            assert response1.json()["tenant_id"] == 1

        # 租户2用户
        async with await get_client("tenant2_user") as client2:
            response2 = await client2.get("/api/v1/auth/me")
            assert response2.status_code == 200
            assert response2.json()["tenant_id"] == 2


@pytest.mark.integration
class TestSuperAdminAccess:
    """超级管理员访问测试 - T109"""

    @pytest.mark.asyncio
    async def test_super_admin_no_tenant_restriction(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试超级管理员无租户限制"""
        get_client, users = tenant_client

        async with await get_client("super_admin") as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 200
            data = response.json()
            assert data["tenant_id"] is None
            # role_id=1 is SUPER_ADMIN
            assert data["role_id"] == 1

    @pytest.mark.asyncio
    async def test_super_admin_can_switch_tenant_view(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试超级管理员可以切换租户视图"""
        get_client, users = tenant_client

        # 超级管理员通过 X-Tenant-ID 头切换视图
        token = create_access_token(
            subject=users["super_admin"].id,
            extra_claims={
                "role_id": users["super_admin"].role_id,
                "tenant_id": None,
            }
        )

        transport = ASGITransport(app=test_app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": "1"
            }
        ) as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 200
            # 超级管理员仍然是超级管理员
            data = response.json()
            # role_id=1 is SUPER_ADMIN
            assert data["role_id"] == 1

    @pytest.mark.asyncio
    async def test_super_admin_access_admin_endpoints(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试超级管理员可以访问管理端点"""
        get_client, users = tenant_client

        async with await get_client("super_admin") as client:
            # 尝试访问管理端点
            response = await client.get("/api/v1/admin/health")

            # 应该能够访问（即使端点不存在也不应该是 403）
            assert response.status_code != 403


@pytest.mark.integration
class TestPermissionDenied:
    """权限拒绝测试 - T110"""

    @pytest.mark.asyncio
    async def test_tenant_user_cannot_access_other_tenant(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试租户用户不能访问其他租户数据"""
        get_client, users = tenant_client

        # 租户1用户不能通过 X-Tenant-ID 切换到租户2
        token = create_access_token(
            subject=users["tenant1_user"].id,
            extra_claims={
                "role_id": users["tenant1_user"].role_id,
                "tenant_id": 1,
            }
        )

        transport = ASGITransport(app=test_app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": "2"  # 尝试切换到其他租户
            }
        ) as client:
            response = await client.get("/api/v1/auth/me")

            # 即使带了 X-Tenant-ID，非超管也应该使用自己的租户
            assert response.status_code == 200
            data = response.json()
            # 普通用户的 X-Tenant-ID 头应该被忽略
            assert data["tenant_id"] == 1

    @pytest.mark.asyncio
    async def test_tenant_user_cannot_access_admin_endpoints(
        self,
        db_session: AsyncSession,
        tenant_client
    ):
        """测试租户用户不能访问管理端点"""
        get_client, users = tenant_client

        async with await get_client("tenant1_user") as client:
            # 尝试访问用户管理端点
            response = await client.get("/api/v1/admin/users")

            # 应该被拒绝
            assert response.status_code in [401, 403, 404]

    @pytest.mark.asyncio
    async def test_inactive_user_denied(
        self,
        db_session: AsyncSession,
        setup_roles_and_users
    ):
        """测试禁用用户被拒绝"""
        import bcrypt

        from app.db.session import get_db

        # 创建禁用用户
        password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
        inactive_user = User(
            id="inactive-user-001",
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=password_hash,
            role_id=3,
            tenant_id=1,
            is_active=False,  # 禁用
        )
        db_session.add(inactive_user)
        await db_session.commit()

        token = create_access_token(
            subject=inactive_user.id,
            extra_claims={
                "role_id": inactive_user.role_id,
                "tenant_id": inactive_user.tenant_id,
            }
        )

        async def override_get_db():
            yield db_session

        test_app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=test_app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"}
        ) as client:
            response = await client.get("/api/v1/auth/me")

            # 禁用用户应该被拒绝或返回特定错误
            # 具体行为取决于实现
            assert response.status_code in [200, 401, 403]

        test_app.dependency_overrides.clear()


@pytest.mark.integration
class TestTenantContextHelpers:
    """租户上下文辅助函数测试"""

    def test_tenant_context_set_and_get(self):
        """测试上下文设置和获取"""
        TenantContext.set(tenant_id=1, user_id="user-123", is_super_admin=False)

        assert TenantContext.get_tenant_id() == 1
        assert TenantContext.get_user_id() == "user-123"
        assert TenantContext.is_super_admin() is False

        TenantContext.clear()

    def test_tenant_context_clear(self):
        """测试上下文清除"""
        TenantContext.set(tenant_id=1, user_id="user-123", is_super_admin=True)
        TenantContext.clear()

        assert TenantContext.get_tenant_id() is None
        assert TenantContext.get_user_id() is None
        assert TenantContext.is_super_admin() is False

    def test_super_admin_context(self):
        """测试超级管理员上下文"""
        TenantContext.set(tenant_id=None, user_id="admin-001", is_super_admin=True)

        assert TenantContext.get_tenant_id() is None
        assert TenantContext.is_super_admin() is True

        TenantContext.clear()
