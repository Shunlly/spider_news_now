"""
多租户中间件 - Multi-tenant Middleware
T111: Tenant filter middleware

提供租户上下文注入和数据隔离支持。
支持超级管理员通过 X-Tenant-ID 头切换租户视图。

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from contextvars import ContextVar
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)

# 上下文变量：存储当前请求的租户上下文
# 使用 ContextVar 确保在异步环境中线程安全
# 注：使用可变默认值是为了简化代码，每次请求会通过 set() 覆盖
_tenant_context: ContextVar[dict[str, Any]] = ContextVar(
    "tenant_context",
    default={"tenant_id": None, "user_id": None, "is_super_admin": False}  # noqa: B039
)


class TenantContext:
    """
    租户上下文管理器

    用于在请求生命周期内存储和访问租户信息。
    支持：
    1. 从 JWT 解析用户的 tenant_id
    2. 超级管理员通过 X-Tenant-ID 头切换视图
    3. 提供给 SQLAlchemy 事件监听器进行自动过滤
    """

    @staticmethod
    def get() -> dict[str, Any]:
        """获取当前租户上下文"""
        return _tenant_context.get()

    @staticmethod
    def get_tenant_id() -> int | None:
        """获取当前租户 ID"""
        return _tenant_context.get().get("tenant_id")

    @staticmethod
    def get_user_id() -> str | None:
        """获取当前用户 ID"""
        return _tenant_context.get().get("user_id")

    @staticmethod
    def is_super_admin() -> bool:
        """检查当前用户是否为超级管理员"""
        return _tenant_context.get().get("is_super_admin", False)

    @staticmethod
    def set(
        tenant_id: int | None = None,
        user_id: str | None = None,
        is_super_admin: bool = False,
    ) -> None:
        """
        设置租户上下文

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            is_super_admin: 是否为超级管理员
        """
        _tenant_context.set({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "is_super_admin": is_super_admin,
        })

    @staticmethod
    def clear() -> None:
        """清除租户上下文"""
        _tenant_context.set({
            "tenant_id": None,
            "user_id": None,
            "is_super_admin": False
        })


# X-Tenant-ID 请求头名称
X_TENANT_ID_HEADER = "X-Tenant-ID"


class TenantMiddleware(BaseHTTPMiddleware):
    """
    租户中间件

    在每个请求开始时：
    1. 解析 JWT Token 获取用户信息
    2. 设置租户上下文
    3. 处理超级管理员的 X-Tenant-ID 头

    在请求结束时清理上下文。
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        处理请求

        流程：
        1. 尝试从请求中获取用户信息（通过 state 或解析 token）
        2. 设置租户上下文
        3. 处理 X-Tenant-ID 头（仅超级管理员）
        4. 调用下一个中间件/路由
        5. 清理上下文
        """
        # 初始化默认上下文
        TenantContext.clear()

        try:
            # 尝试从 Authorization Header 解析用户信息
            await self._set_tenant_context_from_request(request)

            # 调用下一个处理器
            response = await call_next(request)
            return response

        finally:
            # 清理上下文
            TenantContext.clear()

    async def _set_tenant_context_from_request(self, request: Request) -> None:
        """
        从请求中设置租户上下文

        优先级：
        1. 如果用户是超级管理员，检查 X-Tenant-ID 头
        2. 否则使用用户自身的 tenant_id
        """
        from sqlalchemy import select

        from app.core.security import verify_token
        from app.db.session import async_session_maker
        from app.models.user import User

        # 获取 Authorization Header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return

        token = auth_header[7:]  # 移除 "Bearer " 前缀

        # 验证 Token
        user_id = verify_token(token, token_type="access")
        if not user_id:
            return

        # 查询用户信息
        async with async_session_maker() as db:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return

            # 确定租户 ID
            tenant_id = user.tenant_id
            is_super_admin = user.is_super_admin

            # 超级管理员可以通过 X-Tenant-ID 头切换租户视图
            if is_super_admin:
                x_tenant_id = request.headers.get(X_TENANT_ID_HEADER)
                if x_tenant_id:
                    try:
                        tenant_id = int(x_tenant_id)
                        logger.info(
                            "超级管理员切换租户视图",
                            extra={
                                "user_id": user_id,
                                "target_tenant_id": tenant_id
                            }
                        )
                    except ValueError:
                        logger.warning(
                            "无效的 X-Tenant-ID 头",
                            extra={"value": x_tenant_id}
                        )

            # 设置上下文
            TenantContext.set(
                tenant_id=tenant_id,
                user_id=user_id,
                is_super_admin=is_super_admin,
            )

            logger.debug(
                "租户上下文已设置",
                extra={
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "is_super_admin": is_super_admin,
                }
            )


def get_tenant_filter_condition(model: Any) -> Any | None:
    """
    获取租户过滤条件

    用于 SQLAlchemy 查询时自动添加租户过滤。

    Args:
        model: SQLAlchemy 模型类

    Returns:
        过滤条件或 None（超级管理员不过滤）
    """

    ctx = TenantContext.get()

    # 超级管理员且未指定租户 ID 时不过滤
    if ctx.get("is_super_admin") and ctx.get("tenant_id") is None:
        return None

    tenant_id = ctx.get("tenant_id")
    user_id = ctx.get("user_id")

    # 检查模型是否有 tenant_id 字段
    if hasattr(model, "tenant_id"):
        if tenant_id is not None:
            return model.tenant_id == tenant_id
        return None

    # 检查模型是否有 user_id 字段（用户级隔离）
    if hasattr(model, "user_id"):
        if user_id is not None:
            return model.user_id == user_id
        return None

    return None


def apply_tenant_filter(query: Any, model: Any) -> Any:
    """
    应用租户过滤到查询

    Args:
        query: SQLAlchemy 查询对象
        model: 模型类

    Returns:
        添加了租户过滤的查询
    """
    condition = get_tenant_filter_condition(model)
    if condition is not None:
        return query.where(condition)
    return query
