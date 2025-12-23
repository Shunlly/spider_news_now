"""
审计日志装饰器 - Audit Log Decorator
T162: Add audit log decorator for sensitive endpoints

提供用于敏感操作自动记录的装饰器。

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

import functools
from collections.abc import Callable
from typing import Any

from fastapi import Request

from app.core.logging import get_logger
from app.models.audit import AuditAction

logger = get_logger(__name__)


def audit_log(
    action: AuditAction | str,
    resource_type: str,
    get_resource_id: Callable[[dict[str, Any]], str | None] | None = None,
    get_details: Callable[[dict[str, Any], Any], dict] | None = None,
) -> Callable:
    """
    审计日志装饰器

    自动记录敏感端点的操作到审计日志。
    可用于装饰 FastAPI 路由处理函数。

    Args:
        action: 操作类型（AuditAction 枚举或字符串）
        resource_type: 资源类型（如 "user", "tenant", "task"）
        get_resource_id: 可选函数，从路径参数获取资源 ID
        get_details: 可选函数，从参数和响应构建详情

    Example:
        @router.post("/users")
        @audit_log(AuditAction.CREATE, "user")
        async def create_user(...):
            ...

        @router.delete("/users/{user_id}")
        @audit_log(
            AuditAction.DELETE,
            "user",
            get_resource_id=lambda kwargs: kwargs.get("user_id")
        )
        async def delete_user(user_id: str, ...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 尝试获取 Request 对象
            request: Request | None = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            # 尝试获取当前用户
            current_user = kwargs.get("current_user") or kwargs.get("admin")

            # 获取资源 ID
            resource_id = None
            if get_resource_id:
                try:
                    resource_id = get_resource_id(kwargs)
                except Exception:
                    pass

            # 执行原函数
            result = None
            success = True
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # 异步记录审计日志（不阻塞响应）
                try:
                    await _log_audit(
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        request=request,
                        current_user=current_user,
                        result=result,
                        success=success,
                        error_message=error_message,
                        get_details=get_details,
                        kwargs=kwargs,
                    )
                except Exception as log_error:
                    logger.warning(
                        "Failed to create audit log",
                        extra={"error": str(log_error)}
                    )

        return wrapper

    return decorator


async def _log_audit(
    action: AuditAction | str,
    resource_type: str,
    resource_id: str | None,
    request: Request | None,
    current_user: Any,
    result: Any,
    success: bool,
    error_message: str | None,
    get_details: Callable | None,
    kwargs: dict,
) -> None:
    """
    内部函数：创建审计日志记录

    从请求和用户信息中提取必要字段，创建审计日志。
    """
    from app.db.session import async_session_maker
    from app.models.audit import AuditLog

    # 获取 IP 地址
    ip_address = "unknown"
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent")

    # 获取用户信息
    user_id = None
    user_email = None
    if current_user:
        user_id = getattr(current_user, "id", None)
        user_email = getattr(current_user, "email", None)

    # 构建详情
    details = {}
    if get_details:
        try:
            details = get_details(kwargs, result)
        except Exception:
            pass

    # 转换 action 为字符串
    action_value = action.value if isinstance(action, AuditAction) else action

    # 创建日志记录
    async with async_session_maker() as db:
        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action_value,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success,
            error_message=error_message,
        )
        db.add(audit_log)
        await db.commit()

        logger.debug(
            "Audit log created via decorator",
            extra={
                "action": action_value,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "success": success,
            }
        )


def get_audit_context(request: Request | None) -> dict[str, Any]:
    """
    从请求中提取审计上下文

    用于手动记录审计日志时获取请求信息。

    Args:
        request: FastAPI Request 对象

    Returns:
        包含 ip_address 和 user_agent 的字典
    """
    if request is None:
        return {"ip_address": "unknown", "user_agent": None}

    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent"),
    }


class AuditLogger:
    """
    审计日志记录器

    提供便捷的审计日志记录方法，支持上下文管理器。
    """

    def __init__(
        self,
        action: AuditAction,
        resource_type: str,
        request: Request | None = None,
        user: Any = None,
    ):
        self.action = action
        self.resource_type = resource_type
        self.request = request
        self.user = user
        self.resource_id: str | None = None
        self.details: dict = {}
        self.success = True
        self.error_message: str | None = None

    def set_resource_id(self, resource_id: str) -> "AuditLogger":
        """设置资源 ID"""
        self.resource_id = resource_id
        return self

    def set_details(self, details: dict) -> "AuditLogger":
        """设置详情"""
        self.details = details
        return self

    def set_error(self, error_message: str) -> "AuditLogger":
        """设置错误"""
        self.success = False
        self.error_message = error_message
        return self

    async def save(self) -> None:
        """保存审计日志"""
        await _log_audit(
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            request=self.request,
            current_user=self.user,
            result=None,
            success=self.success,
            error_message=self.error_message,
            get_details=lambda *_: self.details,
            kwargs={},
        )
