"""
社交数据订阅管理服务 - Social Data Subscription Management Service

功能：
1. 订阅管理：添加/删除/暂停 Twitter 用户和 Telegram 频道
2. 数据采集：从订阅源获取消息并存储
3. 去重处理：基于 message_hash 避免重复存储
4. 状态跟踪：记录采集进度和统计
"""

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.social_message import SocialMessage
from app.models.social_session import Platform, SessionStatus, SocialSession, TargetType
from app.services.telegram_service import get_telegram_service
from app.services.twitter_service import get_twitter_service

logger = get_logger(__name__)


def generate_message_hash(platform: str, message_id: str, content: str) -> str:
    """
    生成消息哈希，用于去重

    Args:
        platform: 平台名称
        message_id: 消息 ID
        content: 消息内容

    Returns:
        64位哈希字符串
    """
    text = f"{platform}:{message_id}:{content or ''}"
    return hashlib.sha256(text.encode()).hexdigest()


class SocialService:
    """社交数据服务类"""

    # ============== 订阅管理 ==============

    @staticmethod
    async def get_subscriptions(
        db: AsyncSession,
        platform: Platform | None = None,
        status: SessionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        获取订阅列表

        Args:
            db: 数据库会话
            platform: 平台过滤
            status: 状态过滤
            limit: 返回数量
            offset: 偏移量

        Returns:
            {"subscriptions": list, "total": int}
        """
        query = select(SocialSession)

        if platform:
            query = query.where(SocialSession.platform == platform)
        if status:
            query = query.where(SocialSession.status == status)

        # 获取总数
        count_query = select(func.count(SocialSession.id))
        if platform:
            count_query = count_query.where(SocialSession.platform == platform)
        if status:
            count_query = count_query.where(SocialSession.status == status)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 获取列表
        query = query.order_by(SocialSession.created_at.desc())
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        sessions = result.scalars().all()

        return {
            "subscriptions": [
                {
                    "id": s.id,
                    "session_key": s.session_key,
                    "platform": s.platform.value,
                    "target_id": s.target_id,
                    "target_name": s.target_name,
                    "target_username": s.target_username,
                    "target_type": s.target_type.value,
                    "description": s.description,
                    "status": s.status.value,
                    "message_count": s.message_count,
                    "last_message_at": s.last_message_at.isoformat() if s.last_message_at else None,
                    "fetch_interval": s.fetch_interval,
                    "last_fetch_at": s.last_fetch_at.isoformat() if s.last_fetch_at else None,
                    "created_at": s.created_at.isoformat(),
                }
                for s in sessions
            ],
            "total": total,
        }

    @staticmethod
    async def add_twitter_subscription(
        db: AsyncSession,
        user_id: str,
        screen_name: str,
        name: str,
        description: str | None = None,
        fetch_interval: int = 3600,
        owner_user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        添加 Twitter 用户订阅

        Args:
            db: 数据库会话
            user_id: Twitter 用户 ID
            screen_name: 用户名
            name: 显示名称
            description: 订阅描述
            fetch_interval: 采集间隔（秒）
            owner_user_id: 所有者用户 ID（数据隔离）

        Returns:
            {"success": bool, "subscription": dict, "message": str}
        """
        session_key = f"twitter:@{screen_name}"

        # 检查是否已存在（只检查当前用户的订阅）
        check_query = select(SocialSession).where(SocialSession.session_key == session_key)
        if owner_user_id is not None:
            check_query = check_query.where(SocialSession.user_id == owner_user_id)
        result = await db.execute(check_query)
        existing = result.scalars().first()
        if existing:
            return {"success": False, "message": f"已订阅用户 @{screen_name}"}

        # 创建订阅（设置 user_id）
        session = SocialSession(
            user_id=owner_user_id,
            session_key=session_key,
            platform=Platform.TWITTER,
            target_id=user_id,
            target_name=name,
            target_username=f"@{screen_name}",
            target_type=TargetType.USER,
            description=description,
            status=SessionStatus.ACTIVE,
            fetch_interval=fetch_interval,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(f"Added Twitter subscription: @{screen_name}")

        return {
            "success": True,
            "subscription": {
                "id": session.id,
                "session_key": session.session_key,
                "platform": session.platform.value,
                "target_name": session.target_name,
                "target_username": session.target_username,
            },
            "message": f"已订阅 @{screen_name}",
        }

    @staticmethod
    async def add_telegram_subscription(
        db: AsyncSession,
        channel_id: int,
        title: str,
        username: str | None = None,
        target_type: str = "channel",
        description: str | None = None,
        fetch_interval: int = 1800,
        owner_user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        添加 Telegram 频道/群组订阅

        Args:
            db: 数据库会话
            channel_id: 频道/群组 ID
            title: 标题
            username: 用户名
            target_type: 类型 (channel/group)
            description: 订阅描述
            fetch_interval: 采集间隔（秒）
            owner_user_id: 所有者用户 ID（数据隔离）

        Returns:
            {"success": bool, "subscription": dict, "message": str}
        """
        session_key = f"telegram:{channel_id}"

        # 检查是否已存在（只检查当前用户的订阅）
        check_query = select(SocialSession).where(SocialSession.session_key == session_key)
        if owner_user_id is not None:
            check_query = check_query.where(SocialSession.user_id == owner_user_id)
        result = await db.execute(check_query)
        existing = result.scalars().first()
        if existing:
            return {"success": False, "message": f"已订阅频道 {title}"}

        # 映射类型
        type_map = {
            "channel": TargetType.CHANNEL,
            "group": TargetType.GROUP,
            "user": TargetType.USER,
        }

        # 创建订阅（设置 user_id）
        session = SocialSession(
            user_id=owner_user_id,
            session_key=session_key,
            platform=Platform.TELEGRAM,
            target_id=str(channel_id),
            target_name=title,
            target_username=f"@{username}" if username else None,
            target_type=type_map.get(target_type, TargetType.CHANNEL),
            description=description,
            status=SessionStatus.ACTIVE,
            fetch_interval=fetch_interval,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(f"Added Telegram subscription: {title} ({channel_id})")

        return {
            "success": True,
            "subscription": {
                "id": session.id,
                "session_key": session.session_key,
                "platform": session.platform.value,
                "target_name": session.target_name,
                "target_username": session.target_username,
            },
            "message": f"已订阅 {title}",
        }

    @staticmethod
    async def update_subscription(
        db: AsyncSession,
        subscription_id: int,
        status: str | None = None,
        fetch_interval: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        更新订阅配置

        Args:
            db: 数据库会话
            subscription_id: 订阅 ID
            status: 新状态
            fetch_interval: 新采集间隔
            description: 新描述

        Returns:
            {"success": bool, "message": str}
        """
        result = await db.execute(
            select(SocialSession).where(SocialSession.id == subscription_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"success": False, "message": "订阅不存在"}

        if status:
            session.status = SessionStatus(status)
        if fetch_interval is not None:
            session.fetch_interval = fetch_interval
        if description is not None:
            session.description = description

        await db.commit()

        return {"success": True, "message": "更新成功"}

    @staticmethod
    async def delete_subscription(
        db: AsyncSession,
        subscription_id: int,
        delete_messages: bool = False,
    ) -> dict[str, Any]:
        """
        删除订阅

        Args:
            db: 数据库会话
            subscription_id: 订阅 ID
            delete_messages: 是否同时删除消息

        Returns:
            {"success": bool, "message": str}
        """
        result = await db.execute(
            select(SocialSession).where(SocialSession.id == subscription_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"success": False, "message": "订阅不存在"}

        session_key = session.session_key

        if delete_messages:
            # 删除关联的消息
            await db.execute(
                delete(SocialMessage).where(SocialMessage.session_id == subscription_id)
            )

        await db.delete(session)
        await db.commit()

        logger.info(f"Deleted subscription: {session_key}")

        return {"success": True, "message": "删除成功"}

    # ============== 数据采集 ==============

    @staticmethod
    async def fetch_twitter_thread(
        db: AsyncSession,
        session: SocialSession,
        tweet_id: str,
        max_results: int = 100,
    ) -> dict[str, Any]:
        """
        采集 Twitter Thread (T098)

        获取一个对话 Thread 的所有推文，包括原推和所有回复。

        Args:
            db: 数据库会话
            session: 订阅会话（用于关联消息）
            tweet_id: Thread 起始推文 ID
            max_results: 最大获取数量

        Returns:
            {"success": bool, "new_count": int, "total_count": int, "message": str}
        """
        from app.scrapers.twitter_scraper import TwitterScraper
        from app.services.dedup_service import DuplicateService

        try:
            # 创建去重服务
            dedup_service = DuplicateService(db)

            # 创建 Thread 爬虫
            scraper = TwitterScraper(
                session=session,
                db=db,
                dedup_service=dedup_service,
            )

            try:
                # 执行 Thread 采集
                result = await scraper.run_thread(
                    tweet_id=tweet_id,
                    max_results=max_results,
                )

                logger.info(
                    f"Fetched Twitter Thread: {result.get('new', 0)} new from thread {tweet_id}"
                )

                return {
                    "success": True,
                    "new_count": result.get("new", 0),
                    "total_count": result.get("fetched", 0),
                    "duplicate_count": result.get("duplicate", 0),
                    "message": f"获取到 {result.get('new', 0)} 条新推文（共 {result.get('fetched', 0)} 条）",
                }

            finally:
                await scraper.close()

        except Exception as e:
            logger.error(f"Fetch Twitter Thread failed: {e}", exc_info=True)
            return {
                "success": False,
                "new_count": 0,
                "total_count": 0,
                "message": str(e),
            }

    @staticmethod
    async def fetch_telegram_history(
        db: AsyncSession,
        session: SocialSession,
        limit: int = 100,
        min_id: int = 0,
    ) -> dict[str, Any]:
        """
        采集 Telegram 频道历史消息 (T099)

        使用 MTProto API 获取频道历史消息，支持增量采集。

        Args:
            db: 数据库会话
            session: 订阅会话
            limit: 获取消息数量
            min_id: 从此 ID 之后获取（增量采集）

        Returns:
            {"success": bool, "new_count": int, "total_count": int, "message": str}
        """
        from app.scrapers.telegram_scraper import TelegramScraper
        from app.services.dedup_service import DuplicateService

        try:
            # 创建去重服务
            dedup_service = DuplicateService(db)

            # 创建历史采集爬虫
            scraper = TelegramScraper(
                session=session,
                db=db,
                dedup_service=dedup_service,
            )

            try:
                # 执行历史消息采集
                result = await scraper.run_history(
                    limit=limit,
                    min_id=min_id,
                )

                logger.info(
                    f"Fetched Telegram history: {result.get('new', 0)} new from channel {session.target_id}"
                )

                return {
                    "success": True,
                    "new_count": result.get("new", 0),
                    "total_count": result.get("fetched", 0),
                    "duplicate_count": result.get("duplicate", 0),
                    "message": f"获取到 {result.get('new', 0)} 条新消息（共 {result.get('fetched', 0)} 条）",
                }

            finally:
                await scraper.close()

        except Exception as e:
            logger.error(f"Fetch Telegram history failed: {e}", exc_info=True)
            return {
                "success": False,
                "new_count": 0,
                "total_count": 0,
                "message": str(e),
            }

    @staticmethod
    async def fetch_twitter_messages(
        db: AsyncSession,
        session: SocialSession,
        count: int = 50,
    ) -> dict[str, Any]:
        """
        采集 Twitter 用户的推文

        Args:
            db: 数据库会话
            session: 订阅会话
            count: 采集数量

        Returns:
            {"success": bool, "new_count": int, "message": str}
        """
        twitter = get_twitter_service()

        if not twitter.is_connected:
            return {"success": False, "new_count": 0, "message": "Twitter 未连接"}

        try:
            # 获取推文
            result = await twitter.get_user_tweets(
                user_id=session.target_id,
                count=count,
                include_retweets=True,
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "new_count": 0,
                    "message": result.get("message", "获取推文失败"),
                }

            tweets = result.get("tweets", [])
            new_count = 0
            latest_time = session.last_message_at

            for tweet in tweets:
                # 生成哈希
                msg_hash = generate_message_hash(
                    "twitter",
                    tweet.get("id", ""),
                    tweet.get("text", ""),
                )

                # 检查是否已存在
                existing = await db.execute(
                    select(SocialMessage).where(SocialMessage.message_hash == msg_hash)
                )
                if existing.scalar_one_or_none():
                    continue

                # 解析时间
                posted_at = datetime.now()
                if tweet.get("created_at"):
                    try:
                        posted_at = datetime.strptime(tweet["created_at"], "%Y-%m-%d %H:%M")
                    except (ValueError, TypeError, KeyError):
                        pass

                # 更新最新时间
                if not latest_time or posted_at > latest_time:
                    latest_time = posted_at

                # 创建消息记录
                user = tweet.get("user", {})
                message = SocialMessage(
                    session_id=session.id,
                    message_id=tweet.get("id", ""),
                    message_hash=msg_hash,
                    author_id=user.get("id", session.target_id),
                    author_name=user.get("name", session.target_name),
                    author_username=user.get("screen_name"),
                    content=tweet.get("text"),
                    media_urls=json.dumps(
                        [m.get("url") for m in tweet.get("media", []) if m.get("url")]
                    ) if tweet.get("media") else None,
                    reply_count=tweet.get("reply_count", 0),
                    repost_count=tweet.get("retweet_count", 0),
                    like_count=tweet.get("favorite_count", 0),
                    view_count=int(tweet.get("views_count", 0)) if tweet.get("views_count") else 0,
                    repost_of_id=None if not tweet.get("is_retweet") else "retweet",
                    raw_data=json.dumps(tweet),
                    posted_at=posted_at,
                )

                db.add(message)
                new_count += 1

            # 更新会话统计
            session.message_count += new_count
            session.last_fetch_at = datetime.now()
            if latest_time:
                session.last_message_at = latest_time

            await db.commit()

            logger.info(
                f"Fetched Twitter messages: {new_count} new from @{session.target_username}"
            )

            return {
                "success": True,
                "new_count": new_count,
                "message": f"获取到 {new_count} 条新推文",
            }

        except Exception as e:
            logger.error(f"Fetch Twitter messages failed: {e}")
            return {"success": False, "new_count": 0, "message": str(e)}

    @staticmethod
    async def fetch_telegram_messages(
        db: AsyncSession,
        session: SocialSession,
        count: int = 100,
    ) -> dict[str, Any]:
        """
        采集 Telegram 频道的消息

        Args:
            db: 数据库会话
            session: 订阅会话
            count: 采集数量

        Returns:
            {"success": bool, "new_count": int, "message": str}
        """
        telegram = get_telegram_service()

        if not telegram.is_connected:
            return {"success": False, "new_count": 0, "message": "Telegram 未连接"}

        try:
            # 获取消息
            messages = await telegram.get_messages(
                channel_id=int(session.target_id),
                limit=count,
            )

            if not messages:
                return {"success": True, "new_count": 0, "message": "没有新消息"}

            new_count = 0
            latest_time = session.last_message_at

            for msg in messages:
                # 生成哈希
                msg_hash = generate_message_hash(
                    "telegram",
                    str(msg.get("id", "")),
                    msg.get("text", ""),
                )

                # 检查是否已存在
                existing = await db.execute(
                    select(SocialMessage).where(SocialMessage.message_hash == msg_hash)
                )
                if existing.scalar_one_or_none():
                    continue

                # 解析时间
                posted_at = datetime.now()
                if msg.get("date"):
                    try:
                        posted_at = datetime.fromisoformat(msg["date"].replace("Z", "+00:00"))
                        posted_at = posted_at.replace(tzinfo=None)
                    except (ValueError, TypeError, KeyError):
                        pass

                # 更新最新时间
                if not latest_time or posted_at > latest_time:
                    latest_time = posted_at

                # 创建消息记录
                message = SocialMessage(
                    session_id=session.id,
                    message_id=str(msg.get("id", "")),
                    message_hash=msg_hash,
                    author_id=str(msg.get("sender_id", session.target_id)),
                    author_name=session.target_name,
                    author_username=session.target_username,
                    content=msg.get("text"),
                    content_html=msg.get("html"),
                    media_urls=json.dumps(msg.get("urls", [])) if msg.get("urls") else None,
                    view_count=msg.get("views", 0) or 0,
                    repost_count=msg.get("forwards", 0) or 0,
                    reply_to_id=str(msg.get("reply_to_id")) if msg.get("reply_to_id") else None,
                    raw_data=json.dumps(msg),
                    posted_at=posted_at,
                )

                db.add(message)
                new_count += 1

            # 更新会话统计
            session.message_count += new_count
            session.last_fetch_at = datetime.now()
            if latest_time:
                session.last_message_at = latest_time

            await db.commit()

            logger.info(
                f"Fetched Telegram messages: {new_count} new from {session.target_name}"
            )

            return {
                "success": True,
                "new_count": new_count,
                "message": f"获取到 {new_count} 条新消息",
            }

        except Exception as e:
            logger.error(f"Fetch Telegram messages failed: {e}")
            return {"success": False, "new_count": 0, "message": str(e)}

    @staticmethod
    async def fetch_all_active(db: AsyncSession) -> dict[str, Any]:
        """
        采集所有活跃订阅的数据

        Args:
            db: 数据库会话

        Returns:
            {"success": bool, "results": list, "message": str}
        """
        # 获取所有活跃订阅
        result = await db.execute(
            select(SocialSession).where(SocialSession.status == SessionStatus.ACTIVE)
        )
        sessions = result.scalars().all()

        results = []

        for session in sessions:
            now = datetime.now()

            # 检查是否需要采集（根据间隔）
            if session.last_fetch_at:
                elapsed = (now - session.last_fetch_at).total_seconds()
                if elapsed < session.fetch_interval:
                    continue

            # 根据平台采集
            if session.platform == Platform.TWITTER:
                fetch_result = await SocialService.fetch_twitter_messages(db, session)
            elif session.platform == Platform.TELEGRAM:
                fetch_result = await SocialService.fetch_telegram_messages(db, session)
            else:
                continue

            results.append({
                "session_key": session.session_key,
                "platform": session.platform.value,
                "target_name": session.target_name,
                **fetch_result,
            })

        total_new = sum(r.get("new_count", 0) for r in results)

        return {
            "success": True,
            "results": results,
            "message": f"采集完成，共 {total_new} 条新消息",
        }

    # ============== 消息查询 ==============

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        subscription_id: int | None = None,
        platform: Platform | None = None,
        keyword: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """
        获取消息列表

        Args:
            db: 数据库会话
            subscription_id: 订阅 ID 过滤
            platform: 平台过滤
            keyword: 关键词搜索
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            offset: 偏移量
            user_id: 用户 ID 过滤（数据隔离，None = 不过滤）

        Returns:
            {"messages": list, "total": int}
        """
        # 需要 join SocialSession 来应用用户过滤
        query = select(SocialMessage).join(SocialSession)
        count_query = select(func.count(SocialMessage.id)).join(SocialSession)

        # 用户过滤（数据隔离）
        if user_id is not None:
            query = query.where(SocialSession.user_id == user_id)
            count_query = count_query.where(SocialSession.user_id == user_id)

        # 订阅过滤
        if subscription_id:
            query = query.where(SocialMessage.session_id == subscription_id)
            count_query = count_query.where(SocialMessage.session_id == subscription_id)

        # 平台过滤
        if platform:
            query = query.where(SocialSession.platform == platform)
            count_query = count_query.where(SocialSession.platform == platform)

        # 关键词搜索
        if keyword:
            query = query.where(SocialMessage.content.ilike(f"%{keyword}%"))
            count_query = count_query.where(SocialMessage.content.ilike(f"%{keyword}%"))

        # 日期范围
        if start_date:
            query = query.where(SocialMessage.posted_at >= start_date)
            count_query = count_query.where(SocialMessage.posted_at >= start_date)
        if end_date:
            query = query.where(SocialMessage.posted_at <= end_date)
            count_query = count_query.where(SocialMessage.posted_at <= end_date)

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 获取列表
        query = query.order_by(SocialMessage.posted_at.desc())
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        messages = result.scalars().all()

        return {
            "messages": [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "message_id": m.message_id,
                    "author_name": m.author_name,
                    "author_username": m.author_username,
                    "content": m.content,
                    "content_html": m.content_html,
                    "media_urls": json.loads(m.media_urls) if m.media_urls else [],
                    "reply_count": m.reply_count,
                    "repost_count": m.repost_count,
                    "like_count": m.like_count,
                    "view_count": m.view_count,
                    "posted_at": m.posted_at.isoformat() if m.posted_at else None,
                    "fetched_at": m.fetched_at.isoformat() if m.fetched_at else None,
                }
                for m in messages
            ],
            "total": total,
        }

    @staticmethod
    async def get_statistics(db: AsyncSession) -> dict[str, Any]:
        """
        获取统计信息

        Args:
            db: 数据库会话

        Returns:
            统计数据
        """
        # 订阅统计
        subs_result = await db.execute(
            select(
                SocialSession.platform,
                SocialSession.status,
                func.count(SocialSession.id),
            ).group_by(SocialSession.platform, SocialSession.status)
        )
        subs_stats = subs_result.all()

        # 消息统计
        msgs_result = await db.execute(
            select(func.count(SocialMessage.id))
        )
        total_messages = msgs_result.scalar() or 0

        # 今日消息
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await db.execute(
            select(func.count(SocialMessage.id)).where(SocialMessage.posted_at >= today)
        )
        today_messages = today_result.scalar() or 0

        # 构建统计
        platform_stats = {"twitter": 0, "telegram": 0}
        status_stats = {"active": 0, "paused": 0, "error": 0}

        for platform, status, count in subs_stats:
            platform_stats[platform.value] = platform_stats.get(platform.value, 0) + count
            status_stats[status.value] = status_stats.get(status.value, 0) + count

        return {
            "subscriptions": {
                "total": sum(platform_stats.values()),
                "by_platform": platform_stats,
                "by_status": status_stats,
            },
            "messages": {
                "total": total_messages,
                "today": today_messages,
            },
        }
