"""
Telegram 爬虫实现
Telegram Scraper Implementation

支持两种模式：
1. Bot API 模式 - 获取 Bot 收到的更新（实时消息）
2. MTProto 模式 - 获取频道历史消息（需要用户授权）

功能：
- 频道/群组消息采集
- 历史消息回溯 (T099)
- 增量采集（offset/min_id）
- 媒体 URL 提取
- 消息互动数据（浏览数、转发数）
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


class TelegramScraper(BaseSocialScraper):
    """
    Telegram 爬虫

    支持功能：
    - 频道/群组消息采集
    - **历史消息回溯** (T099 - 使用 MTProto API)
    - 增量采集（offset）
    - 媒体 URL 提取
    - 消息互动数据（浏览数）

    工作模式：
    - Bot API: 实时消息推送（需要 Bot Token）
    - MTProto: 历史消息获取（需要用户授权的 TelegramService）
    """

    # Telegram Bot API 端点
    BASE_URL = "https://api.telegram.org"

    def __init__(
        self,
        session: SocialSession,
        db: AsyncSession,
        bot_token: str | None = None,
        dedup_service: DuplicateService | None = None,
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
        self._client: httpx.AsyncClient | None = None
        self._bot_info: dict[str, Any] | None = None

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
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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

    async def get_bot_info(self) -> dict[str, Any]:
        """获取 Bot 信息"""
        if self._bot_info is None:
            self._bot_info = await self._call_api("getMe")
        return self._bot_info

    async def fetch_messages(
        self,
        since_id: str | None = None,
        max_results: int = 100,
    ) -> list[dict[str, Any]]:
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
                # 检查是否是目标频道/群组 (Telegram 超级群组 ID 以 -100 开头)
                normalized_chat_id = chat_id.removeprefix("-100") if chat_id.startswith("-100") else chat_id
                if chat_id == self.session.target_id or normalized_chat_id == self.session.target_id:
                    message["_update_id"] = update.get("update_id")
                    messages.append(message)

        return messages

    async def get_channel_history(
        self,
        limit: int = 100,
        min_id: int = 0,
    ) -> list[dict[str, Any]]:
        """
        获取频道历史消息（使用 MTProto API）(T099)

        通过 TelegramService 获取频道历史消息，支持增量采集。

        Args:
            limit: 获取消息数量
            min_id: 最小消息 ID（用于增量采集）

        Returns:
            消息列表（MTProto 格式）
        """
        from app.services.telegram_service import get_telegram_service

        telegram = get_telegram_service()

        if not telegram.is_connected:
            self.logger.warning("TelegramService 未连接，无法获取历史消息")
            return []

        try:
            channel_id = int(self.session.target_id)
            messages = await telegram.get_messages(
                channel_id=channel_id,
                limit=limit,
                offset_id=min_id,
            )

            self.logger.info(
                f"获取到 {len(messages)} 条历史消息",
                extra={"channel_id": channel_id, "min_id": min_id},
            )

            return messages

        except Exception as e:
            self.logger.error(f"获取历史消息失败: {e}")
            return []

    async def fetch_messages_mtproto(
        self,
        limit: int = 100,
        min_id: int = 0,
    ) -> list[dict[str, Any]]:
        """
        使用 MTProto API 获取消息（推荐）

        这是 T099 的核心实现，使用 Telethon 客户端获取频道历史消息。

        Args:
            limit: 获取消息数量
            min_id: 从此 ID 之后获取（增量采集）

        Returns:
            标准化的消息列表
        """
        raw_messages = await self.get_channel_history(limit=limit, min_id=min_id)

        # 转换为标准格式
        parsed_messages = []
        for raw in raw_messages:
            try:
                parsed = self._parse_mtproto_message(raw)
                if parsed:
                    parsed_messages.append(parsed)
            except Exception as e:
                self.logger.warning(f"解析 MTProto 消息失败: {e}")
                continue

        return parsed_messages

    def _parse_mtproto_message(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """
        解析 MTProto 消息为标准格式

        将 TelegramService.get_messages() 返回的消息转换为爬虫标准格式。

        Args:
            raw: TelegramService 返回的消息字典

        Returns:
            标准化的消息字典
        """
        if not raw:
            return None

        message_id = str(raw.get("id", ""))
        if not message_id:
            return None

        # 解析时间
        date_str = raw.get("date")
        if date_str:
            try:
                posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                posted_at = posted_at.replace(tzinfo=None)
            except (ValueError, TypeError):
                posted_at = datetime.now()
        else:
            posted_at = datetime.now()

        # 解析媒体
        media_urls = raw.get("urls", [])
        media_type = raw.get("media_type")
        if media_type:
            # 标记媒体类型
            media_urls = [f"{media_type}:{url}" if not url.startswith("http") else url for url in media_urls]

        return {
            "message_id": message_id,
            "author_id": str(raw.get("sender_id", self.session.target_id)),
            "author_name": self.session.target_name,
            "author_username": self.session.target_username,
            "content": raw.get("text", ""),
            "content_html": raw.get("html"),
            "media_urls": media_urls,
            "reply_count": 0,
            "repost_count": raw.get("forwards", 0) or 0,
            "like_count": 0,
            "view_count": raw.get("views", 0) or 0,
            "reply_to_id": str(raw.get("reply_to_id")) if raw.get("reply_to_id") else None,
            "repost_of_id": None,
            "posted_at": posted_at,
            "raw_data": raw,
        }

    async def run_history(
        self,
        limit: int = 100,
        min_id: int = 0,
    ) -> dict[str, Any]:
        """
        执行历史消息采集流程 (T099)

        完整流程：
        1. 使用 MTProto API 获取历史消息
        2. 解析和标准化消息
        3. 去重检查
        4. 存储到数据库
        5. 更新会话统计

        Args:
            limit: 获取消息数量
            min_id: 增量采集起始 ID

        Returns:
            采集结果统计
        """
        start_time = datetime.now()
        result = {
            "session_id": self.session.id,
            "platform": self.platform.value,
            "channel_id": self.session.target_id,
            "fetched": 0,
            "new": 0,
            "duplicate": 0,
            "failed": 0,
            "duration_seconds": 0,
            "error": None,
        }

        try:
            # 获取历史消息
            raw_messages = await self.get_channel_history(limit=limit, min_id=min_id)
            result["fetched"] = len(raw_messages)

            if not raw_messages:
                self.logger.info("无历史消息")
                return result

            new_messages = []
            for raw in raw_messages:
                try:
                    # 解析消息
                    parsed = self._parse_mtproto_message(raw)
                    if not parsed:
                        result["failed"] += 1
                        continue

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
                    self.logger.error(f"处理消息失败: {e}", exc_info=True)
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
                f"历史消息采集完成: 获取 {result['fetched']}, "
                f"新增 {result['new']}, "
                f"重复 {result['duplicate']}, "
                f"失败 {result['failed']}",
            )

            return result

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"历史消息采集失败: {e}", exc_info=True)
            raise

    async def parse_message(self, raw_message: dict[str, Any]) -> dict[str, Any]:
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
        entities: list[dict[str, Any]],
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

    async def get_file_url(self, file_id: str) -> str | None:
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
    dedup_service: DuplicateService | None = None,
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
