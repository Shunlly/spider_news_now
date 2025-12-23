"""
Common Layer - 通用层

包含跨模块共享的组件：
- middleware: 中间件（租户上下文、限流等）
- deps: FastAPI 依赖注入函数
"""

# Middleware
# Dependencies
from app.common.deps import (
    get_current_active_user,
    get_current_user,
    get_optional_user,
    require_admin,
    require_permission,
    require_role,
    require_super_admin,
)
from app.common.middleware import (
    RateLimitMiddleware,
    TenantContext,
    TenantMiddleware,
    apply_tenant_filter,
    get_tenant_filter_condition,
)

__all__ = [
    # Middleware
    "TenantMiddleware",
    "TenantContext",
    "RateLimitMiddleware",
    "get_tenant_filter_condition",
    "apply_tenant_filter",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_permission",
    "require_role",
    "require_admin",
    "require_super_admin",
]
