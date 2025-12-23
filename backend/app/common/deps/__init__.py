"""
Dependencies Package - 依赖注入包

包含 FastAPI 路由保护所需的依赖函数。
"""

from app.common.deps.auth import (
    get_current_active_user,
    get_current_user,
    get_optional_user,
    oauth2_scheme,
    require_admin,
    require_permission,
    require_role,
    require_super_admin,
)

__all__ = [
    "oauth2_scheme",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_permission",
    "require_role",
    "require_admin",
    "require_super_admin",
]
