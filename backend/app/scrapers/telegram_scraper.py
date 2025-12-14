"""
Telegram 爬虫实现
Telegram Scraper Implementation

使用 Telegram Bot API 获取频道/群组消息。
支持增量采集和媒体下载。
"""

import json
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


class TelegramScraper(BaseSocialScraper):
    """
    Telegram Bot API 爬虫

    支持功能：
    - 频道/群组消息采集
    - 增量采集（offset）
    - 媒体 URL 提取
    - 消息互动数据（浏览数）
    """

    # Telegram Bot API 端点
    BASE_URL = "https://api.telegram.org"

    def __init__(
        self,
        session: SocialSession,
        db: AsyncSession,
        bot_token: Optional[str] = None,
        dedup_service: Optional[DuplicateService] = None,
    ):
        """
        初始化 Telegram 爬虫

        Args:
            session: 社交会话
            db: 数据库会话
            bot_token: Telegram Bot Token
            dedup_service: 去重服务
        """
        super().__init__(
            platform=Platform.TELEGRAM,
            session=session,
            db=db,
            dedup_service=dedup_service,
        )
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self._client: Optional[httpx.AsyncClient] = None
        self._bot_info: Optional[Dict[str, Any]] = None

    @property
    def api_url(self) -> str:
        """获取 Bot API URL"""
        return f"{self.BASE_URL}/bot{self.bot_token}"

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
            )
        return self._client

    async def _call_api(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        调用 Telegram Bot API

        Args:
            method: API 方法名
            params: 请求参数

        Returns:
            API 响应数据
        """
        client = await self._get_client()
        url = f"{self.api_url}/{method}"

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                error_desc = data.get("description", "Unknown error")
                raise Exception(f"Telegram API 错误: {error_desc}")

            return data.get("result", {})

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.logger.error("Telegram Bot Token 无效")
            elif e.response.status_code == 429:
                self.logger.warning("Telegram API 限流")
            raise
        except Exception as e:
            self.logger.error(f"Telegram API 调用失败: {e}")
            raise

    async def get_bot_info(self) -> Dict[str, Any]:
        """获取 Bot 信息"""
        if self._bot_info is None:
            self._bot_info = await self._call_api("getMe")
        return self._bot_info

    async def fetch_messages(
        self,
        since_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取频道/群组消息

        使用 getUpdates 方法获取消息。
        注意：Bot 必须是频道/群组的成员才能获取消息。

        对于公开频道，也可以使用 forwardMessage 方法获取历史消息。

        Args:
            since_id: 从此更新 ID 之后获取
            max_results: 最大获取数量

        Returns:
            消息列表
        """
        # 构建请求参数
        params = {
            "limit": min(max_results, 100),
            "allowed_updates": json.dumps(["message", "channel_post"]),
        }

        if since_id:
            params["offset"] = int(since_id) + 1

        # 获取更新
        updates = await self._call_api("getUpdates", params)

        # 过滤出目标频道/群组的消息
        messages = []
        for update in updates:
            message = update.get("message") or update.get("channel_post")
            if message:
                chat_id = str(message.get("chat", {}).get("id", ""))
                # 检查是否是目标频道/群组
                if chat_id == self.session.target_id or chat_id.lstrip("-100") == self.session.target_id:
                    message["_update_id"] = update.get("update_id")
                    messages.append(message)

        return messages

    async def get_channel_history(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取频道历史消息（需要 Bot 有 getChatHistory 权限）

        注意：标准 Bot API 不支持获取历史消息。
        如需获取历史消息，需要使用 MTProto API (Telethon/Pyrogram)。

        这里提供一个占位实现，实际使用时需要替换为 MTProto 实现。
        """
        self.logger.warning(
            "标准 Bot API 不支持获取历史消息。"
            "如需获取历史消息，请使用 MTProto API。"
        )
        return []

    async def parse_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 Telegram 消息为标准格式

        Args:
            raw_message: Telegram API 返回的消息数据

        Returns:
            标准化的消息字典
        """
        message_id = str(raw_message.get("message_id", ""))

        # 获取发送者信息
        sender = raw_message.get("from") or raw_message.get("sender_chat", {})
        author_id = str(sender.get("id", ""))
        author_name = (
            sender.get("title")  # 频道名称
            or f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
            or "Unknown"
        )
        author_username = sender.get("username")

        # 解析内容
        content = raw_message.get("text") or raw_message.get("caption", "")

        # 解析 HTML 格式（entities）
        content_html = self._parse_entities(
            content,
            raw_message.get("entities") or raw_message.get("caption_entities", [])
        )

        # 解析媒体 URL
        media_urls = []
        photo = raw_message.get("photo")
        if photo:
            # 获取最大尺寸的图片
            largest_photo = max(photo, key=lambda p: p.get("file_size", 0))
            file_id = largest_photo.get("file_id")
            if file_id:
                # 需要调用 getFile 获取下载链接
                media_urls.append(f"file_id:{file_id}")

        video = raw_message.get("video")
        if video:
            file_id = video.get("file_id")
            if file_id:
                media_urls.append(f"file_id:{file_id}")

        document = raw_message.get("document")
        if document:
            file_id = document.get("file_id")
            if file_id:
                media_urls.append(f"file_id:{file_id}")

        # 解析时间
        date = raw_message.get("date")
        if date:
            posted_at = datetime.fromtimestamp(date)
        else:
            posted_at = datetime.now()

        # 解析回复关系
        reply_to_id = None
        reply_to = raw_message.get("reply_to_message")
        if reply_to:
            reply_to_id = str(reply_to.get("message_id", ""))

        # 解析转发关系
        repost_of_id = None
        forward_from = raw_message.get("forward_from_message_id")
        if forward_from:
            repost_of_id = str(forward_from)

        # 获取浏览数（仅频道消息有此字段）
        view_count = raw_message.get("views", 0)

        return {
            "message_id": message_id,
            "author_id": author_id,
            "author_name": author_name,
            "author_username": author_username,
            "content": content,
            "content_html": content_html if content_html != content else None,
            "media_urls": media_urls,
            "reply_count": 0,  # Telegram API 不提供回复数
            "repost_count": 0,  # Telegram API 不提供转发数
            "like_count": 0,  # Telegram API 不提供点赞数
            "view_count": view_count,
            "reply_to_id": reply_to_id,
            "repost_of_id": repost_of_id,
            "posted_at": posted_at,
            "raw_data": raw_message,
        }

    def _parse_entities(
        self,
        text: str,
        entities: List[Dict[str, Any]],
    ) -> str:
        """
        将 Telegram 实体解析为 HTML

        Args:
            text: 原始文本
            entities: 实体列表

        Returns:
            HTML 格式的文本
        """
        if not entities or not text:
            return text

        # 按 offset 逆序排列，从后向前替换避免位置偏移
        sorted_entities = sorted(entities, key=lambda e: e["offset"], reverse=True)

        result = text
        for entity in sorted_entities:
            offset = entity["offset"]
            length = entity["length"]
            entity_type = entity["type"]
            entity_text = text[offset:offset + length]

            if entity_type == "bold":
                replacement = f"<b>{entity_text}</b>"
            elif entity_type == "italic":
                replacement = f"<i>{entity_text}</i>"
            elif entity_type == "underline":
                replacement = f"<u>{entity_text}</u>"
            elif entity_type == "strikethrough":
                replacement = f"<s>{entity_text}</s>"
            elif entity_type == "code":
                replacement = f"<code>{entity_text}</code>"
            elif entity_type == "pre":
                replacement = f"<pre>{entity_text}</pre>"
            elif entity_type == "text_link":
                url = entity.get("url", "")
                replacement = f'<a href="{url}">{entity_text}</a>'
            elif entity_type == "text_mention":
                user = entity.get("user", {})
                user_id = user.get("id", "")
                replacement = f'<a href="tg://user?id={user_id}">{entity_text}</a>'
            elif entity_type == "mention":
                replacement = f'<a href="https://t.me/{entity_text[1:]}">{entity_text}</a>'
            elif entity_type == "hashtag":
                replacement = f'<span class="hashtag">{entity_text}</span>'
            elif entity_type == "url":
                replacement = f'<a href="{entity_text}">{entity_text}</a>'
            else:
                continue

            result = result[:offset] + replacement + result[offset + length:]

        return result

    async def get_file_url(self, file_id: str) -> Optional[str]:
        """
        获取文件下载 URL

        Args:
            file_id: Telegram 文件 ID

        Returns:
            文件下载 URL
        """
        try:
            file_info = await self._call_api("getFile", {"file_id": file_id})
            file_path = file_info.get("file_path")
            if file_path:
                return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        except Exception as e:
            self.logger.error(f"获取文件 URL 失败: {e}")
        return None

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


async def create_telegram_scraper(
    session: SocialSession,
    db: AsyncSession,
    dedup_service: Optional[DuplicateService] = None,
) -> TelegramScraper:
    """
    工厂函数：创建 Telegram 爬虫实例

    Args:
        session: 社交会话
        db: 数据库会话
        dedup_service: 去重服务

    Returns:
        TelegramScraper 实例
    """
    return TelegramScraper(
        session=session,
        db=db,
        dedup_service=dedup_service,
    )
