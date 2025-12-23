"""
系统维护任务 - Maintenance Celery Tasks
定期清理过期数据

遵循宪法要求：
- 类型提示完整
- 中文注释说明核心逻辑
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.models.captcha import CAPTCHA_CONFIG, CaptchaAttempt
from app.models.export_task import ExportStatus, ExportTask
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_captcha_attempts")
def cleanup_captcha_attempts() -> dict[str, Any]:
    """
    清理过期的验证码尝试记录

    删除超过24小时的验证码尝试记录，减少数据库存储压力。

    Returns:
        清理结果统计
    """
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_cleanup_captcha_async())
        return result
    finally:
        loop.close()


async def _cleanup_captcha_async() -> dict[str, Any]:
    """
    异步清理验证码记录
    """
    retention_seconds = CAPTCHA_CONFIG["record_retention_seconds"]
    cutoff_time = datetime.utcnow() - timedelta(seconds=retention_seconds)

    async with async_session_factory() as session:
        try:
            # 删除过期记录
            stmt = delete(CaptchaAttempt).where(
                CaptchaAttempt.created_at < cutoff_time
            )
            result = await session.execute(stmt)
            deleted_count = result.rowcount

            await session.commit()

            logger.info(f"验证码记录清理完成: 删除 {deleted_count} 条记录")
            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "cutoff_time": cutoff_time.isoformat(),
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"验证码记录清理失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_expired_exports")
def cleanup_expired_exports() -> dict[str, Any]:
    """
    清理过期的导出文件

    删除超过配置天数的导出文件和数据库记录。

    Returns:
        清理结果统计
    """
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(_cleanup_exports_async())
        return result
    finally:
        loop.close()


async def _cleanup_exports_async() -> dict[str, Any]:
    """
    异步清理导出文件
    """
    cleanup_days = settings.EXPORT_CLEANUP_DAYS
    cutoff_time = datetime.utcnow() - timedelta(days=cleanup_days)

    files_deleted = 0
    records_deleted = 0
    errors = []

    async with async_session_factory() as session:
        try:
            # 查询过期的导出任务
            stmt = select(ExportTask).where(
                ExportTask.created_at < cutoff_time,
                ExportTask.status == ExportStatus.COMPLETED,
            )
            result = await session.execute(stmt)
            expired_tasks = result.scalars().all()

            # 删除文件
            for task in expired_tasks:
                if task.file_path:
                    try:
                        file_path = Path(task.file_path)
                        if file_path.exists():
                            os.remove(file_path)
                            files_deleted += 1
                    except Exception as e:
                        errors.append(f"删除文件失败 {task.file_path}: {e}")

            # 删除数据库记录
            delete_stmt = delete(ExportTask).where(
                ExportTask.created_at < cutoff_time,
                ExportTask.status == ExportStatus.COMPLETED,
            )
            result = await session.execute(delete_stmt)
            records_deleted = result.rowcount

            await session.commit()

            logger.info(
                f"导出文件清理完成: 文件={files_deleted}, 记录={records_deleted}"
            )
            return {
                "status": "completed",
                "files_deleted": files_deleted,
                "records_deleted": records_deleted,
                "errors": errors if errors else None,
                "cutoff_time": cutoff_time.isoformat(),
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"导出文件清理失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "files_deleted": files_deleted,
            }


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_old_audit_logs")
def cleanup_old_audit_logs(retention_days: int = 90) -> dict[str, Any]:
    """
    清理旧的审计日志

    默认保留90天的审计日志。

    Args:
        retention_days: 保留天数

    Returns:
        清理结果统计
    """
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            _cleanup_audit_logs_async(retention_days)
        )
        return result
    finally:
        loop.close()


async def _cleanup_audit_logs_async(retention_days: int) -> dict[str, Any]:
    """
    异步清理审计日志
    """
    from app.models.audit import AuditLog

    cutoff_time = datetime.utcnow() - timedelta(days=retention_days)

    async with async_session_factory() as session:
        try:
            stmt = delete(AuditLog).where(AuditLog.created_at < cutoff_time)
            result = await session.execute(stmt)
            deleted_count = result.rowcount

            await session.commit()

            logger.info(f"审计日志清理完成: 删除 {deleted_count} 条记录")
            return {
                "status": "completed",
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "cutoff_time": cutoff_time.isoformat(),
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"审计日志清理失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }
