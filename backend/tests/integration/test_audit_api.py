"""
审计日志 API 集成测试 - Audit Log API Integration Tests
T159: Integration test for audit log endpoint

测试审计日志 API 功能：
- 获取审计日志列表
- 按用户/操作/资源类型筛选
- 权限检查
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.role import Role, RoleType
from app.models.user import User
from tests.conftest import test_app


@pytest.fixture
async def setup_audit_data(db_session: AsyncSession, test_user: User):
    """创建审计日志测试数据"""
    # 创建审计日志
    logs = [
        AuditLog(
            user_id=test_user.id,
            action="login",
            resource_type="user",
            resource_id=test_user.id,
            details={"method": "password"},
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
        ),
        AuditLog(
            user_id=test_user.id,
            action="create_article",
            resource_type="article",
            resource_id="article-001",
            details={"title": "Test Article"},
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
        ),
        AuditLog(
            user_id=test_user.id,
            action="delete_article",
            resource_type="article",
            resource_id="article-002",
            details={"reason": "spam"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        ),
        AuditLog(
            user_id=None,  # 系统操作，无用户
            action="system_cleanup",
            resource_type="system",
            resource_id="cleanup-001",
            details={},
            ip_address="10.0.0.1",
            user_agent="system/1.0",
        ),
    ]

    for log in logs:
        db_session.add(log)
    await db_session.commit()

    return logs


@pytest.fixture
async def setup_roles(db_session: AsyncSession):
    """创建角色 - 使用 merge 避免冲突"""
    from sqlalchemy import select

    roles_data = [
        (1, RoleType.SUPER_ADMIN.value, "超级管理员", ["*"]),
        (2, RoleType.TENANT_ADMIN.value, "租户管理员", ["tenant:*"]),
        (3, RoleType.USER.value, "用户", ["task:read"]),
    ]

    roles = []
    for role_id, name, display_name, permissions in roles_data:
        # 检查角色是否已存在
        result = await db_session.execute(select(Role).where(Role.id == role_id))
        existing = result.scalar_one_or_none()
        if existing:
            roles.append(existing)
        else:
            role = Role(id=role_id, name=name, display_name=display_name, permissions=permissions)
            db_session.add(role)
            roles.append(role)

    await db_session.commit()
    return roles


@pytest.fixture
async def super_admin_user(db_session: AsyncSession):
    """创建超级管理员用户"""
    import bcrypt
    from sqlalchemy import select

    # 确保超级管理员角色存在
    result = await db_session.execute(select(Role).where(Role.id == 1))
    existing = result.scalar_one_or_none()
    if not existing:
        role = Role(id=1, name=RoleType.SUPER_ADMIN.value, display_name="超级管理员", permissions=["*"])
        db_session.add(role)
        await db_session.flush()

    password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()

    user = User(
        id="super-admin-audit-test-001",
        username="superadmin_audit",
        email="superadmin@audit.com",
        password_hash=password_hash,
        role_id=1,  # 超级管理员
        tenant_id=None,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_client(db_session: AsyncSession, super_admin_user: User):
    """创建超级管理员客户端"""
    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject=super_admin_user.id,
        extra_claims={
            "role_id": super_admin_user.role_id,
            "tenant_id": None,
        }
    )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as client:
        yield client

    test_app.dependency_overrides.clear()


@pytest.fixture
async def regular_client(db_session: AsyncSession):
    """创建普通用户客户端"""
    import bcrypt
    from sqlalchemy import select

    # 确保普通用户角色存在
    result = await db_session.execute(select(Role).where(Role.id == 3))
    existing = result.scalar_one_or_none()
    if not existing:
        role = Role(id=3, name=RoleType.USER.value, display_name="用户", permissions=["task:read"])
        db_session.add(role)
        await db_session.flush()

    password_hash = bcrypt.hashpw(b"user123", bcrypt.gensalt()).decode()

    user = User(
        id="regular-user-audit-test-001",
        username="regularuser_audit",
        email="regular@audit.com",
        password_hash=password_hash,
        role_id=3,  # 普通用户
        tenant_id=None,  # 不设置租户，避免外键约束问题
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    token = create_access_token(
        subject=user.id,
        extra_claims={
            "role_id": user.role_id,
            "tenant_id": user.tenant_id,
        }
    )

    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as client:
        yield client

    test_app.dependency_overrides.clear()


@pytest.mark.integration
class TestAuditLogAPI:
    """审计日志 API 集成测试"""

    @pytest.mark.asyncio
    async def test_get_audit_logs_success(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
    ):
        """测试获取审计日志 - 成功"""
        response = await admin_client.get("/api/v1/admin/audit-logs")

        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] >= 4  # 至少有我们创建的 4 条日志

    @pytest.mark.asyncio
    async def test_get_audit_logs_pagination(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
    ):
        """测试审计日志分页"""
        # 第一页
        response1 = await admin_client.get("/api/v1/admin/audit-logs?page=1&page_size=2")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["logs"]) <= 2
        assert data1["page"] == 1

        # 第二页
        response2 = await admin_client.get("/api/v1/admin/audit-logs?page=2&page_size=2")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["page"] == 2

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_user(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
        test_user: User,
    ):
        """测试按用户 ID 筛选"""
        response = await admin_client.get(f"/api/v1/admin/audit-logs?user_id={test_user.id}")

        assert response.status_code == 200
        data = response.json()
        # 所有返回的日志都应该是该用户的
        for log in data["logs"]:
            assert log["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_action(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
    ):
        """测试按操作类型筛选"""
        response = await admin_client.get("/api/v1/admin/audit-logs?action=login")

        assert response.status_code == 200
        data = response.json()
        # 所有返回的日志都应该是 login 操作
        for log in data["logs"]:
            assert log["action"] == "login"

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_resource_type(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
    ):
        """测试按资源类型筛选"""
        response = await admin_client.get("/api/v1/admin/audit-logs?resource_type=article")

        assert response.status_code == 200
        data = response.json()
        # 所有返回的日志都应该是 article 资源类型
        for log in data["logs"]:
            assert log["resource_type"] == "article"

    @pytest.mark.asyncio
    async def test_get_audit_logs_combined_filters(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
        test_user: User,
    ):
        """测试组合筛选"""
        response = await admin_client.get(
            f"/api/v1/admin/audit-logs?user_id={test_user.id}&action=create_article&resource_type=article"
        )

        assert response.status_code == 200
        data = response.json()
        # 所有返回的日志都应该匹配所有筛选条件
        for log in data["logs"]:
            assert log["user_id"] == test_user.id
            assert log["action"] == "create_article"
            assert log["resource_type"] == "article"

    @pytest.mark.asyncio
    async def test_get_audit_logs_includes_username(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
        test_user: User,
    ):
        """测试日志包含用户名"""
        response = await admin_client.get(f"/api/v1/admin/audit-logs?user_id={test_user.id}")

        assert response.status_code == 200
        data = response.json()
        # 有用户 ID 的日志应该包含用户名
        for log in data["logs"]:
            if log["user_id"] == test_user.id:
                assert log["username"] == test_user.username

    @pytest.mark.asyncio
    async def test_get_audit_logs_order_by_created_at(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
    ):
        """测试按创建时间倒序"""
        response = await admin_client.get("/api/v1/admin/audit-logs")

        assert response.status_code == 200
        data = response.json()
        logs = data["logs"]

        # 验证按时间倒序
        for i in range(len(logs) - 1):
            assert logs[i]["created_at"] >= logs[i + 1]["created_at"]


@pytest.mark.integration
class TestAuditLogPermissions:
    """审计日志权限测试"""

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access(
        self,
        regular_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试普通用户不能访问审计日志"""
        response = await regular_client.get("/api/v1/admin/audit-logs")

        # 应该被拒绝
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access(self, db_session: AsyncSession):
        """测试未认证用户不能访问"""
        async def override_get_db():
            yield db_session

        test_app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/admin/audit-logs")

        test_app.dependency_overrides.clear()

        assert response.status_code == 401


@pytest.mark.integration
class TestAuditLogDataIntegrity:
    """审计日志数据完整性测试"""

    @pytest.mark.asyncio
    async def test_log_contains_required_fields(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
        setup_audit_data,
    ):
        """测试日志包含所有必要字段"""
        response = await admin_client.get("/api/v1/admin/audit-logs")

        assert response.status_code == 200
        data = response.json()

        for log in data["logs"]:
            assert "id" in log
            assert "action" in log
            assert "created_at" in log
            # 可选字段
            assert "user_id" in log
            assert "username" in log
            assert "resource_type" in log
            assert "resource_id" in log
            assert "details" in log
            assert "ip_address" in log
            assert "user_agent" in log

    @pytest.mark.asyncio
    async def test_empty_result_valid_response(
        self,
        admin_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """测试空结果返回有效响应"""
        # 使用不存在的用户 ID
        response = await admin_client.get("/api/v1/admin/audit-logs?user_id=nonexistent-user-id")

        assert response.status_code == 200
        data = response.json()
        assert data["logs"] == []
        assert data["total"] == 0
