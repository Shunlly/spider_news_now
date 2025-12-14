"""
社交媒体爬虫基类
Social Media Scraper Base Class

遵循宪法 II.B 异构数据建模：
- 社交数据采用 Session 模式
- 支持多账号轮换
- 支持代理池
"""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.social_session import Platform, SessionStatus, SocialSession
from app.models.social_message import SocialMessage
from app.services.dedup_service import DuplicateService

logger = get_logger(__name__)


class BaseSocialScraper(ABC):
    """
    社交媒体爬虫抽象基类

    所有社交平台爬虫必须继承此类并实现 fetch_messages 方法。
    提供通用的消息处理、去重、存储功能。
    """

    def __init__(
        self,
        platform: Platform,
        session: SocialSession,
        db: AsyncSession,
        dedup_service: Optional[DuplicateService] = None,
    ):
        """
        初始化社交爬虫

        Args:
            platform: 社交平台类型
            session: 关联的社交会话
            db: 数据库会话
            dedup_service: 去重服务实例
        """
        self.platform = platform
        self.session = session
        self.db = db
        self.dedup_service = dedup_service
        self.logger = get_logger(f"{__name__}.{platform.value}")

    @abstractmethod
    async def fetch_messages(
        self,
        since_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        从平台获取消息

        子类必须实现此方法，调用平台 API 获取原始消息数据。

        Args:
            since_id: 从此 ID 之后获取消息（增量采集）
            max_results: 最大获取数量

        Returns:
            原始消息字典列表，每个字典包含平台返回的原始数据
        """
        pass

    @abstractmethod
    async def parse_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析原始消息为标准格式

        子类必须实现此方法，将平台特定的消息格式转换为统一格式。

        Args:
            raw_message: 平台返回的原始消息数据

        Returns:
            标准化的消息字典，包含以下字段：
            - message_id: 平台消息 ID
            - author_id: 发送者 ID
            - author_name: 发送者显示名
            - author_username: 发送者用户名（可选）
            - content: 文本内容
            - content_html: HTML 格式内容（可选）
            - media_urls: 媒体 URL 列表
            - reply_count: 回复数
            - repost_count: 转发数
            - like_count: 点赞数
            - view_count: 浏览数
            - reply_to_id: 回复的消息 ID（可选）
            - repost_of_id: 转发的原消息 ID（可选）
            - posted_at: 发布时间
            - raw_data: 原始 JSON 数据
        """
        pass

    def compute_message_hash(self, message_id: str) -> str:
        """
        计算消息哈希（用于去重）

        使用 session_key + message_id 组合计算哈希，
        确保跨会话的消息不会被误判为重复。
        """
        unique_key = f"{self.session.session_key}:{message_id}"
        return hashlib.sha256(unique_key.encode("utf-8")).hexdigest()

    def validate_message(self, message: Dict[str, Any]) -> bool:
        """
        验证消息数据完整性

        Args:
            message: 标准化后的消息字典

        Returns:
            True 表示有效，False 表示无效
        """
        required_fields = ["message_id", "author_id", "author_name", "posted_at"]

        for field in required_fields:
            if field not in message or message[field] is None:
                self.logger.warning(f"消息缺少必填字段: {field}")
                return False

        # 至少要有内容或媒体
        if not message.get("content") and not message.get("media_urls"):
            self.logger.warning("消息无内容且无媒体附件")
            return False

        return True

    async def run(
        self,
        since_id: Optional[str] = None,
        max_results: int = 100,
    ) -> Dict[str, Any]:
        """
        执行采集流程

        完整流程：
        1. 调用 fetch_messages 获取原始消息
        2. 解析和标准化消息
        3. 去重检查
        4. 存储到数据库
        5. 更新会话统计

        Args:
            since_id: 增量采集起始 ID
            max_results: 最大获取数量

        Returns:
            采集结果统计
        """
        start_time = datetime.now()
        result = {
            "session_id": self.session.id,
            "platform": self.platform.value,
            "fetched": 0,
            "new": 0,
            "duplicate": 0,
            "failed": 0,
            "duration_seconds": 0,
            "error": None,
        }

        try:
            self.logger.info(
                f"开始采集会话: {self.session.session_key}",
                extra={"session_id": self.session.id, "since_id": since_id},
            )

            # 1. 获取原始消息
            raw_messages = await self.fetch_messages(
                since_id=since_id,
                max_results=max_results,
            )
            result["fetched"] = len(raw_messages)

            if not raw_messages:
                self.logger.info("无新消息")
                return result

            # 2. 解析和处理消息
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

            # 3. 批量存储
            if new_messages:
                self.db.add_all(new_messages)
                result["new"] = len(new_messages)

            # 4. 更新会话统计
            self.session.message_count += result["new"]
            self.session.last_fetch_at = datetime.now()
            if new_messages:
                # 获取最新消息的时间
                latest_time = max(m.posted_at for m in new_messages)
                if (
                    self.session.last_message_at is None
                    or latest_time > self.session.last_message_at
                ):
                    self.session.last_message_at = latest_time

            await self.db.commit()

            # 计算耗时
            result["duration_seconds"] = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"采集完成: 获取 {result['fetched']}, "
                f"新增 {result['new']}, "
                f"重复 {result['duplicate']}, "
                f"失败 {result['failed']}",
                extra={
                    "session_id": self.session.id,
                    **result,
                },
            )

            return result

        except Exception as e:
            result["error"] = str(e)
            self.session.status = SessionStatus.ERROR
            await self.db.commit()

            self.logger.error(
                f"采集失败: {e}",
                extra={"session_id": self.session.id},
                exc_info=True,
            )
            raise
