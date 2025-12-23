"""
Twitter 爬虫实现
Twitter Scraper Implementation

使用 Twitter API v2 获取用户时间线和对话 Thread。
支持增量采集、Thread 采集和媒体下载。

功能：
1. 用户时间线采集 (User Timeline)
2. 对话 Thread 采集 (Conversation Thread)
3. 单条推文获取
"""

import json
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.social_message import SocialMessage
from app.models.social_session import Platform, SocialSession
from app.scrapers.social_base import BaseSocialScraper
from app.services.dedup_service import DuplicateService

logger = get_logger(__name__)


class TwitterScraper(BaseSocialScraper):
    """
    Twitter API v2 爬虫

    支持功能：
    - 用户时间线采集
    - **对话 Thread 采集** (T098)
    - 增量采集（since_id）
    - 媒体 URL 提取
    - 互动数据（点赞、转发、回复）
    """

    # Twitter API v2 端点
    BASE_URL = "https://api.twitter.com/2"

    # 请求字段配置
    TWEET_FIELDS = [
        "id",
        "text",
        "created_at",
        "author_id",
        "conversation_id",
        "in_reply_to_user_id",
        "referenced_tweets",
        "attachments",
        "public_metrics",
        "entities",
    ]

    USER_FIELDS = [
        "id",
        "name",
        "username",
        "profile_image_url",
    ]

    MEDIA_FIELDS = [
        "media_key",
        "type",
        "url",
        "preview_image_url",
    ]

    EXPANSIONS = [
        "author_id",
        "attachments.media_keys",
        "referenced_tweets.id",
    ]

    def __init__(
        self,
        session: SocialSession,
        db: AsyncSession,
        bearer_token: str | None = None,
        dedup_service: DuplicateService | None = None,
    ):
        """
        初始化 Twitter 爬虫

        Args:
            session: 社交会话
            db: 数据库会话
            bearer_token: Twitter API Bearer Token
            dedup_service: 去重服务
        """
        super().__init__(
            platform=Platform.TWITTER,
            session=session,
            db=db,
            dedup_service=dedup_service,
        )
        self.bearer_token = bearer_token or settings.TWITTER_BEARER_TOKEN
        self._client: httpx.AsyncClient | None = None
        self._users_cache: dict[str, dict[str, Any]] = {}
        self._media_cache: dict[str, dict[str, Any]] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.bearer_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def fetch_messages(
        self,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        获取用户时间线推文

        调用 Twitter API v2 的 users/{id}/tweets 端点。

        Args:
            since_id: 从此推文 ID 之后获取
            max_results: 最大获取数量（10-100）

        Returns:
            推文列表
        """
        client = await self._get_client()

        # 构建请求参数
        params = {
            "max_results": min(max_results, 100),
            "tweet.fields": ",".join(self.TWEET_FIELDS),
            "user.fields": ",".join(self.USER_FIELDS),
            "media.fields": ",".join(self.MEDIA_FIELDS),
            "expansions": ",".join(self.EXPANSIONS),
        }

        if since_id:
            params["since_id"] = since_id

        # 请求用户时间线
        url = f"{self.BASE_URL}/users/{self.session.target_id}/tweets"

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 缓存用户和媒体信息
            self._cache_includes(data)

            return data.get("data", [])

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # 限流处理
                self.logger.warning("Twitter API 限流，稍后重试")
                raise
            elif e.response.status_code == 401:
                self.logger.error("Twitter API 认证失败，请检查 Bearer Token")
                raise
            else:
                self.logger.error(f"Twitter API 错误: {e.response.text}")
                raise
        except Exception as e:
            self.logger.error(f"请求 Twitter API 失败: {e}")
            raise

    # ==================== Thread 采集功能 (T098) ====================

    async def fetch_tweet(self, tweet_id: str) -> dict[str, Any] | None:
        """
        获取单条推文详情

        用于获取推文的 conversation_id，以便后续采集整个 Thread。

        Args:
            tweet_id: 推文 ID

        Returns:
            推文数据字典，失败返回 None
        """
        client = await self._get_client()

        params = {
            "tweet.fields": ",".join(self.TWEET_FIELDS),
            "user.fields": ",".join(self.USER_FIELDS),
            "media.fields": ",".join(self.MEDIA_FIELDS),
            "expansions": ",".join(self.EXPANSIONS),
        }

        url = f"{self.BASE_URL}/tweets/{tweet_id}"

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 缓存用户和媒体信息
            self._cache_includes(data)

            return data.get("data")

        except httpx.HTTPStatusError as e:
            self.logger.error(f"获取推文 {tweet_id} 失败: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"请求推文 {tweet_id} 失败: {e}")
            return None

    async def fetch_thread(
        self,
        tweet_id: str,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
        """
        获取完整对话 Thread

        流程：
        1. 获取指定推文，提取 conversation_id
        2. 使用 Search API 搜索该 conversation 的所有推文
        3. 返回按时间排序的完整 Thread

        Args:
            tweet_id: Thread 中任意一条推文的 ID
            max_results: 最大获取数量（10-100）

        Returns:
            Thread 中所有推文的列表，按时间升序排列
        """
        # 1. 获取起始推文，提取 conversation_id
        tweet = await self.fetch_tweet(tweet_id)
        if not tweet:
            self.logger.error(f"无法获取推文 {tweet_id}")
            return []

        conversation_id = tweet.get("conversation_id")
        if not conversation_id:
            self.logger.warning(f"推文 {tweet_id} 无 conversation_id，仅返回单条推文")
            return [tweet]

        self.logger.info(f"获取 Thread: conversation_id={conversation_id}")

        # 2. 搜索该 conversation 的所有推文
        query = f"conversation_id:{conversation_id}"
        thread_tweets = await self._search_tweets(query, max_results=max_results)

        # 3. 确保包含原始推文（搜索可能不返回）
        tweet_ids = {t["id"] for t in thread_tweets}
        if tweet_id not in tweet_ids:
            thread_tweets.append(tweet)

        # 4. 按时间排序（升序，最早的在前）
        thread_tweets.sort(
            key=lambda t: t.get("created_at", ""),
            reverse=False,
        )

        self.logger.info(f"Thread 获取完成: {len(thread_tweets)} 条推文")
        return thread_tweets

    async def _search_tweets(
        self,
        query: str,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        使用 Search API 搜索推文

        使用 Twitter API v2 的 tweets/search/recent 端点。
        注意：只能搜索最近 7 天的推文。

        Args:
            query: 搜索查询字符串（如 "conversation_id:123456"）
            max_results: 每次请求最大数量（10-100）
            next_token: 分页 token

        Returns:
            匹配的推文列表
        """
        client = await self._get_client()

        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": ",".join(self.TWEET_FIELDS),
            "user.fields": ",".join(self.USER_FIELDS),
            "media.fields": ",".join(self.MEDIA_FIELDS),
            "expansions": ",".join(self.EXPANSIONS),
        }

        if next_token:
            params["next_token"] = next_token

        url = f"{self.BASE_URL}/tweets/search/recent"

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 缓存用户和媒体信息
            self._cache_includes(data)

            tweets = data.get("data", [])

            # 处理分页（递归获取更多结果）
            meta = data.get("meta", {})
            if meta.get("next_token") and len(tweets) >= max_results // 2:
                more_tweets = await self._search_tweets(
                    query=query,
                    max_results=max_results,
                    next_token=meta["next_token"],
                )
                tweets.extend(more_tweets)

            return tweets

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                self.logger.warning("Twitter Search API 限流")
                raise
            else:
                self.logger.error(f"Twitter Search API 错误: {e.response.text}")
                return []
        except Exception as e:
            self.logger.error(f"搜索推文失败: {e}")
            return []

    def _cache_includes(self, data: dict[str, Any]) -> None:
        """缓存 API 响应中的 includes 数据（用户和媒体）"""
        if "includes" in data:
            if "users" in data["includes"]:
                for user in data["includes"]["users"]:
                    self._users_cache[user["id"]] = user
            if "media" in data["includes"]:
                for media in data["includes"]["media"]:
                    self._media_cache[media["media_key"]] = media

    async def run_thread(
        self,
        tweet_id: str,
        max_results: int = 100,
    ) -> dict[str, Any]:
        """
        执行 Thread 采集流程

        完整流程：
        1. 获取 Thread 所有推文
        2. 解析和标准化消息
        3. 去重检查
        4. 存储到数据库
        5. 更新会话统计

        Args:
            tweet_id: Thread 起始推文 ID
            max_results: 最大获取数量

        Returns:
            采集结果统计
        """
        # 获取 Thread
        raw_messages = await self.fetch_thread(tweet_id, max_results)

        # 调用基类的 run 方法处理后续流程（需要临时替换 fetch_messages）
        # 这里直接处理，保持与基类一致的逻辑
        start_time = datetime.now()
        result = {
            "session_id": self.session.id,
            "platform": self.platform.value,
            "thread_id": tweet_id,
            "fetched": len(raw_messages),
            "new": 0,
            "duplicate": 0,
            "failed": 0,
            "duration_seconds": 0,
            "error": None,
        }

        try:
            if not raw_messages:
                self.logger.info("Thread 无推文")
                return result

            new_messages = []
            for raw_message in raw_messages:
                try:
                    # 解析消息
                    parsed = await self.parse_message(raw_message)

                    # 验证消息
                    if not self.validate_message(parsed):
                        result["failed"] += 1
                        continue

                    # 计算哈希
                    message_hash = self.compute_message_hash(parsed["message_id"])

                    # 去重检查
                    if self.dedup_service:
                        exists = await self.dedup_service.check_bloom_filter(message_hash)
                        if exists:
                            result["duplicate"] += 1
                            continue

                    # 创建消息记录
                    message = SocialMessage(
                        session_id=self.session.id,
                        message_id=parsed["message_id"],
                        message_hash=message_hash,
                        author_id=parsed["author_id"],
                        author_name=parsed["author_name"],
                        author_username=parsed.get("author_username"),
                        content=parsed.get("content"),
                        content_html=parsed.get("content_html"),
                        media_urls=json.dumps(parsed.get("media_urls", [])),
                        media_local_paths=None,
                        reply_count=parsed.get("reply_count", 0),
                        repost_count=parsed.get("repost_count", 0),
                        like_count=parsed.get("like_count", 0),
                        view_count=parsed.get("view_count", 0),
                        reply_to_id=parsed.get("reply_to_id"),
                        repost_of_id=parsed.get("repost_of_id"),
                        raw_data=json.dumps(parsed.get("raw_data", {})),
                        posted_at=parsed["posted_at"],
                    )

                    new_messages.append(message)

                    # 添加到 Bloom Filter
                    if self.dedup_service:
                        await self.dedup_service.add_to_bloom_filter(message_hash)

                except Exception as e:
                    self.logger.error(f"解析消息失败: {e}", exc_info=True)
                    result["failed"] += 1
                    continue

            # 批量存储
            if new_messages:
                self.db.add_all(new_messages)
                result["new"] = len(new_messages)

            # 更新会话统计
            self.session.message_count += result["new"]
            self.session.last_fetch_at = datetime.now()
            if new_messages:
                latest_time = max(m.posted_at for m in new_messages)
                if (
                    self.session.last_message_at is None
                    or latest_time > self.session.last_message_at
                ):
                    self.session.last_message_at = latest_time

            await self.db.commit()

            result["duration_seconds"] = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Thread 采集完成: 获取 {result['fetched']}, "
                f"新增 {result['new']}, "
                f"重复 {result['duplicate']}, "
                f"失败 {result['failed']}",
            )

            return result

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Thread 采集失败: {e}", exc_info=True)
            raise

    # ==================== 消息解析 ====================

    async def parse_message(self, raw_message: dict[str, Any]) -> dict[str, Any]:
        """
        解析推文为标准格式

        将 Twitter API v2 返回的推文数据转换为统一的消息格式。

        Args:
            raw_message: Twitter API 返回的原始推文数据

        Returns:
            标准化的消息字典
        """
        tweet_id = raw_message["id"]
        author_id = raw_message["author_id"]

        # 获取作者信息
        author = self._users_cache.get(author_id, {})
        author_name = author.get("name", "Unknown")
        author_username = author.get("username")

        # 解析内容
        content = raw_message.get("text", "")

        # 解析媒体 URL
        media_urls = []
        attachments = raw_message.get("attachments", {})
        media_keys = attachments.get("media_keys", [])
        for media_key in media_keys:
            media = self._media_cache.get(media_key, {})
            if media.get("url"):
                media_urls.append(media["url"])
            elif media.get("preview_image_url"):
                media_urls.append(media["preview_image_url"])

        # 解析互动数据
        metrics = raw_message.get("public_metrics", {})

        # 解析引用关系
        reply_to_id = None
        repost_of_id = None
        referenced_tweets = raw_message.get("referenced_tweets", [])
        for ref in referenced_tweets:
            if ref["type"] == "replied_to":
                reply_to_id = ref["id"]
            elif ref["type"] == "retweeted":
                repost_of_id = ref["id"]

        # 解析时间
        created_at = raw_message.get("created_at")
        if created_at:
            posted_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            posted_at = datetime.now()

        return {
            "message_id": tweet_id,
            "author_id": author_id,
            "author_name": author_name,
            "author_username": author_username,
            "content": content,
            "content_html": None,  # Twitter 不返回 HTML
            "media_urls": media_urls,
            "reply_count": metrics.get("reply_count", 0),
            "repost_count": metrics.get("retweet_count", 0),
            "like_count": metrics.get("like_count", 0),
            "view_count": metrics.get("impression_count", 0),
            "reply_to_id": reply_to_id,
            "repost_of_id": repost_of_id,
            "posted_at": posted_at,
            "raw_data": raw_message,
        }

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


async def create_twitter_scraper(
    session: SocialSession,
    db: AsyncSession,
    dedup_service: DuplicateService | None = None,
) -> TwitterScraper:
    """
    工厂函数：创建 Twitter 爬虫实例

    Args:
        session: 社交会话
        db: 数据库会话
        dedup_service: 去重服务

    Returns:
        TwitterScraper 实例
    """
    return TwitterScraper(
        session=session,
        db=db,
        dedup_service=dedup_service,
    )
