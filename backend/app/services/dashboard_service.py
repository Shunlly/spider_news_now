"""
Dashboard 服务 - Dashboard Service
T134: Dashboard stats service

提供 Dashboard 统计数据服务。
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.news_article import NewsArticle
from app.models.news_source import NewsSource
from app.models.quota import Quota
from app.models.scraper_run import ScraperRun
from app.models.social_message import SocialMessage
from app.models.social_session import SessionStatus, SocialSession

logger = get_logger(__name__)


class DashboardService:
    """
    Dashboard 统计服务

    提供系统整体统计数据，支持实时更新。
    """

    async def get_stats(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> dict:
        """
        获取 Dashboard 统计数据

        Args:
            db: 数据库会话
            user_id: 用户 ID（用于过滤非管理员数据）
            is_admin: 是否为管理员

        Returns:
            统计数据字典
        """
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 构建用户过滤条件
        user_filter = []
        if not is_admin and user_id:
            user_filter.append(NewsArticle.user_id == user_id)

        # 文章总数
        total_articles_stmt = select(func.count()).select_from(NewsArticle)
        if user_filter:
            total_articles_stmt = total_articles_stmt.where(*user_filter)
        total_articles_result = await db.execute(total_articles_stmt)
        total_articles = total_articles_result.scalar() or 0

        # 今日文章数
        today_articles_stmt = (
            select(func.count())
            .select_from(NewsArticle)
            .where(NewsArticle.created_at >= today_start)
        )
        if user_filter:
            today_articles_stmt = today_articles_stmt.where(*user_filter)
        today_articles_result = await db.execute(today_articles_stmt)
        articles_today = today_articles_result.scalar() or 0

        # 爬虫源统计
        sources_stmt = select(func.count()).select_from(NewsSource)
        if not is_admin and user_id:
            sources_stmt = sources_stmt.where(NewsSource.user_id == user_id)
        sources_result = await db.execute(sources_stmt)
        total_scrapers = sources_result.scalar() or 0

        # 活跃爬虫（最近 24 小时有运行）
        active_scrapers_stmt = (
            select(func.count(func.distinct(ScraperRun.source_key)))
            .select_from(ScraperRun)
            .where(ScraperRun.started_at >= now - timedelta(hours=24))
        )
        active_scrapers_result = await db.execute(active_scrapers_stmt)
        active_scrapers = active_scrapers_result.scalar() or 0

        # 社交会话统计
        social_session_filter = []
        if not is_admin and user_id:
            social_session_filter.append(SocialSession.user_id == user_id)

        active_sessions_stmt = (
            select(func.count())
            .select_from(SocialSession)
            .where(SocialSession.status == SessionStatus.ACTIVE)
        )
        if social_session_filter:
            active_sessions_stmt = active_sessions_stmt.where(*social_session_filter)
        active_sessions_result = await db.execute(active_sessions_stmt)
        active_social_sessions = active_sessions_result.scalar() or 0

        # 社交消息总数
        if is_admin:
            total_messages_stmt = select(func.count()).select_from(SocialMessage)
        else:
            total_messages_stmt = (
                select(func.count())
                .select_from(SocialMessage)
                .join(SocialSession)
            )
            if user_id:
                total_messages_stmt = total_messages_stmt.where(SocialSession.user_id == user_id)
        total_messages_result = await db.execute(total_messages_stmt)
        total_social_messages = total_messages_result.scalar() or 0

        # 配额信息
        quota_used = 0
        quota_limit = 100
        if user_id:
            quota_stmt = select(Quota).where(Quota.user_id == user_id)
            quota_result = await db.execute(quota_stmt)
            quota = quota_result.scalar_one_or_none()
            if quota:
                quota_used = quota.daily_used
                quota_limit = quota.daily_limit

        return {
            "total_articles": total_articles,
            "articles_today": articles_today,
            "active_scrapers": active_scrapers,
            "total_scrapers": total_scrapers,
            "active_social_sessions": active_social_sessions,
            "total_social_messages": total_social_messages,
            "quota_used": quota_used,
            "quota_limit": quota_limit,
            "timestamp": now.isoformat(),
        }

    async def get_recent_activity(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        is_admin: bool = False,
        limit: int = 10,
    ) -> list[dict]:
        """
        获取最近活动

        Args:
            db: 数据库会话
            user_id: 用户 ID
            is_admin: 是否为管理员
            limit: 返回数量

        Returns:
            活动列表
        """
        activities = []

        # 最近爬虫运行
        runs_stmt = (
            select(ScraperRun)
            .order_by(ScraperRun.started_at.desc())
            .limit(limit)
        )
        runs_result = await db.execute(runs_stmt)
        runs = runs_result.scalars().all()

        for run in runs:
            status_emoji = "✅" if run.status == "success" else "❌" if run.status == "failed" else "🔄"
            activities.append({
                "type": "scraper_run",
                "icon": status_emoji,
                "message": f"{run.source_key} 采集 {run.articles_new} 篇新文章",
                "timestamp": run.started_at.isoformat() if run.started_at else None,
                "status": run.status,
            })

        # 按时间排序
        activities.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

        return activities[:limit]

    async def get_scraper_status_list(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        is_admin: bool = False,
    ) -> list[dict]:
        """
        获取爬虫状态列表

        Args:
            db: 数据库会话
            user_id: 用户 ID
            is_admin: 是否为管理员

        Returns:
            爬虫状态列表
        """
        # 获取所有爬虫源
        sources_stmt = select(NewsSource)
        if not is_admin and user_id:
            sources_stmt = sources_stmt.where(NewsSource.user_id == user_id)
        sources_result = await db.execute(sources_stmt)
        sources = sources_result.scalars().all()

        status_list = []
        for source in sources:
            # 获取最近一次运行
            last_run_stmt = (
                select(ScraperRun)
                .where(ScraperRun.source_key == source.source_key)
                .order_by(ScraperRun.started_at.desc())
                .limit(1)
            )
            last_run_result = await db.execute(last_run_stmt)
            last_run = last_run_result.scalar_one_or_none()

            status_list.append({
                "source_key": source.source_key,
                "display_name": source.display_name,
                "enabled": source.enabled,
                "status": last_run.status if last_run else "idle",
                "last_run": last_run.started_at.isoformat() if last_run and last_run.started_at else None,
                "articles_scraped": last_run.articles_new if last_run else 0,
                "error_message": last_run.error_message if last_run else None,
            })

        return status_list


# 全局服务实例
dashboard_service = DashboardService()
