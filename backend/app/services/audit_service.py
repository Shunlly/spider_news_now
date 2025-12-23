"""
审计日志服务 - Audit Log Service
Security Audit Logging

提供审计日志记录功能：
1. 自动记录敏感操作
2. 支持异步写入
3. 提供查询接口

遵循宪法要求：
- 完整类型提示
- 中文注释说明核心逻辑
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit import AuditAction, AuditLog

logger = get_logger(__name__)


class AuditService:
    """
    审计服务

    记录系统中的敏感操作，用于安全审计和问题排查。
    """

    async def log(
        self,
        db: AsyncSession,
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
    ) -> AuditLog:
        """
        记录审计日志

        Args:
            db: 数据库会话
            action: 操作类型
            resource_type: 资源类型（如 user, task, news）
            ip_address: 来源 IP 地址
            user_id: 操作用户 ID
            user_email: 用户邮箱快照
            resource_id: 被操作的资源 ID
            user_agent: 用户代理字符串
            details: 额外详情（JSON）
            description: 操作描述
            success: 是否成功
            error_message: 错误消息

        Returns:
            创建的 AuditLog 实例
        """
        audit_log = AuditLog.create_log(
            action=action,
            resource_type=resource_type,
            ip_address=ip_address,
            user_id=user_id,
            user_email=user_email,
            resource_id=resource_id,
            user_agent=user_agent,
            details=details,
            description=description,
            success=success,
            error_message=error_message,
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        logger.debug(
            "Audit log created",
            extra={
                "action": action.value if isinstance(action, AuditAction) else action,
                "resource_type": resource_type,
                "user_id": user_id,
            }
        )

        return audit_log

    async def log_login(
        self,
        db: AsyncSession,
        user_id: str,
        user_email: str,
        ip_address: str,
        user_agent: str | None = None,
        success: bool = True,
        error_message: str | None = None,
    ) -> AuditLog:
        """
        记录登录审计日志

        Args:
            db: 数据库会话
            user_id: 用户 ID
            user_email: 用户邮箱
            ip_address: 来源 IP
            user_agent: 用户代理
            success: 是否成功
            error_message: 错误消息（如果失败）

        Returns:
            AuditLog 实例
        """
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        return await self.log(
            db=db,
            action=action,
            resource_type="auth",
            ip_address=ip_address,
            user_id=user_id if success else None,
            user_email=user_email,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
            description=f"用户 {user_email} {'登录成功' if success else '登录失败'}",
        )

    async def log_logout(
        self,
        db: AsyncSession,
        user_id: str,
        user_email: str,
        ip_address: str,
        user_agent: str | None = None,
    ) -> AuditLog:
        """记录登出审计日志"""
        return await self.log(
            db=db,
            action=AuditAction.LOGOUT,
            resource_type="auth",
            ip_address=ip_address,
            user_id=user_id,
            user_email=user_email,
            user_agent=user_agent,
            description=f"用户 {user_email} 登出",
        )

    async def log_resource_action(
        self,
        db: AsyncSession,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_id: str,
        ip_address: str,
        user_email: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """
        记录资源操作审计日志

        用于记录 CRUD 操作。
        """
        action_map = {
            AuditAction.CREATE: "创建",
            AuditAction.READ: "读取",
            AuditAction.UPDATE: "更新",
            AuditAction.DELETE: "删除",
            AuditAction.EXPORT: "导出",
        }
        action_text = action_map.get(action, action.value)

        return await self.log(
            db=db,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_id=user_id,
            user_email=user_email,
            user_agent=user_agent,
            details=details,
            description=f"{action_text} {resource_type}:{resource_id}",
        )

    async def get_user_logs(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """
        获取用户的审计日志

        Args:
            db: 数据库会话
            user_id: 用户 ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            审计日志列表
        """
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_logs(
        self,
        db: AsyncSession,
        hours: int = 24,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        获取最近的审计日志

        Args:
            db: 数据库会话
            hours: 时间范围（小时）
            action: 过滤操作类型
            resource_type: 过滤资源类型
            limit: 返回数量限制

        Returns:
            审计日志列表
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        stmt = select(AuditLog).where(AuditLog.created_at >= cutoff)

        if action:
            stmt = stmt.where(AuditLog.action == action.value)

        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)

        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_failed_login_attempts(
        self,
        db: AsyncSession,
        ip_address: str | None = None,
        hours: int = 1,
    ) -> int:
        """
        获取失败登录尝试次数

        用于检测暴力破解攻击。

        Args:
            db: 数据库会话
            ip_address: 可选 IP 地址过滤
            hours: 时间范围

        Returns:
            失败次数
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        stmt = select(func.count(AuditLog.id)).where(
            AuditLog.action == AuditAction.LOGIN_FAILED.value,
            AuditLog.created_at >= cutoff,
        )

        if ip_address:
            stmt = stmt.where(AuditLog.ip_address == ip_address)

        result = await db.execute(stmt)
        return result.scalar() or 0


# 全局服务实例
audit_service = AuditService()
