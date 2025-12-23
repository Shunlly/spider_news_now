"""
审计日志模型 - AuditLog SQLAlchemy Model
Audit Log Model for Security Auditing

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑

记录所有敏感操作，用于安全审计和问题排查。
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditAction(str, Enum):
    """
    审计操作类型枚举

    记录系统中所有敏感操作类型
    """
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"

    # CRUD 操作
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # 特殊操作
    EXPORT = "export"
    CONFIG_CHANGE = "config_change"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"

    # 任务操作
    TASK_RUN = "task_run"
    TASK_CANCEL = "task_cancel"


class AuditLog(Base):
    """
    审计日志实体 - 记录所有敏感操作

    用于安全审计、问题排查和合规要求。
    建议保留至少90天的审计日志。
    """

    __tablename__ = "audit_logs"

    # 主键 - 自增整数
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True,
        comment="日志ID"
    )

    # 用户外键 - 操作执行者，可为空（如系统操作）
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True,
        comment="操作用户ID"
    )

    # 用户邮箱快照 - 即使用户被删除也能追溯
    user_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="用户邮箱（快照）"
    )

    # 操作类型
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="操作类型"
    )

    # 资源类型 - 被操作的资源类型（如 user, task, news）
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="资源类型"
    )

    # 资源ID - 被操作的资源ID
    resource_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="资源ID"
    )

    # 来源IP地址
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=False,
        comment="来源IP地址"
    )

    # 用户代理
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="用户代理字符串"
    )

    # 操作详情 - JSON格式存储额外信息
    details: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={},
        comment="操作详情"
    )

    # 操作结果描述
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="操作描述"
    )

    # 是否成功
    success: Mapped[bool] = mapped_column(
        default=True, nullable=False,
        comment="操作是否成功"
    )

    # 错误消息（如果操作失败）
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="错误消息"
    )

    # 操作时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), index=True,
        comment="操作时间"
    )

    # 关联关系
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"resource='{self.resource_type}:{self.resource_id}')>"
        )

    @classmethod
    def create_log(
        cls,
        action: AuditAction,
        resource_type: str,
        ip_address: str,
        user_id: str | None = None,
        user_email: str | None = None,
        resource_id: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
        description: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> "AuditLog":
        """
        创建审计日志记录

        Args:
            action: 操作类型
            resource_type: 资源类型
            ip_address: 来源IP
            user_id: 操作用户ID
            user_email: 用户邮箱快照
            resource_id: 资源ID
            user_agent: 用户代理
            details: 额外详情
            description: 操作描述
            success: 是否成功
            error_message: 错误消息

        Returns:
            AuditLog 实例
        """
        return cls(
            user_id=user_id,
            user_email=user_email,
            action=action.value if isinstance(action, AuditAction) else action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            description=description,
            success=success,
            error_message=error_message,
        )
