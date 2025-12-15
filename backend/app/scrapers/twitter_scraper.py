"""
Twitter 爬虫实现
Twitter Scraper Implementation

使用 Twitter API v2 获取用户时间线。
支持增量采集和媒体下载。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.social_session import Platform, SocialSession
from app.scrapers.social_base import BaseSocialScraper
from app.services.dedup_service import DuplicateService

logger = get_logger(__name__)


class TwitterScraper(BaseSocialScraper):
    """
    Twitter API v2 爬虫

    支持功能：
    - 用户时间线采集
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
        bearer_token: Optional[str] = None,
        dedup_service: Optional[DuplicateService] = None,
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
        self._client: Optional[httpx.AsyncClient] = None
        self._users_cache: Dict[str, Dict[str, Any]] = {}
        self._media_cache: Dict[str, Dict[str, Any]] = {}

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
        since_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
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

            # 缓存用户信息
            if "includes" in data:
                if "users" in data["includes"]:
                    for user in data["includes"]["users"]:
                        self._users_cache[user["id"]] = user
                if "media" in data["includes"]:
                    for media in data["includes"]["media"]:
                        self._media_cache[media["media_key"]] = media

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

    async def parse_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
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
    dedup_service: Optional[DuplicateService] = None,
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
