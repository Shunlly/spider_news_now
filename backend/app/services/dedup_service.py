"""
去重检测服务 - Redis Bloom Filter + SimHash 实现
Duplicate Detection Service - Redis Bloom Filter + SimHash Implementation

遵循宪法 II.C 全局去重机制要求：
- URL 指纹：使用 SHA256 哈希 + Redis Bloom Filter
- 内容指纹：使用 SimHash 算法检测相似内容

去重流程：
1. 计算 URL 的 SHA256 哈希
2. 通过 Bloom Filter 快速判断是否存在（O(1) 时间复杂度）
3. 如果 Bloom Filter 返回"可能存在"，则查询数据库二次确认（处理假阳性）
4. 可选：计算内容 SimHash，检测相似内容
"""

import hashlib
import logging
import re
from typing import List, Optional, Set, Tuple

import redis.asyncio as redis
from simhash import Simhash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.news_article import NewsArticle

logger = logging.getLogger(__name__)


class DuplicateService:
    """
    去重检测服务

    使用 Redis Bloom Filter 实现高效的 URL 去重，
    使用 SimHash 算法检测相似内容。
    """

    # Bloom Filter 的 Redis Key
    BLOOM_FILTER_KEY = "dedup:url_hash:bloom"

    # SimHash 汉明距离阈值（距离 <= 3 被认为是相似内容）
    SIMHASH_THRESHOLD = 3

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化去重服务

        Args:
            redis_client: Redis 异步客户端实例，如不提供则自动创建
        """
        self._redis: Optional[redis.Redis] = redis_client
        self._bloom_initialized = False

    async def _get_redis(self) -> redis.Redis:
        """
        获取 Redis 客户端（懒加载）

        使用连接池确保连接复用，避免频繁创建连接。
        """
        if self._redis is None:
            self._redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,
            )
        return self._redis

    async def _ensure_bloom_filter(self) -> None:
        """
        确保 Bloom Filter 已初始化

        Bloom Filter 参数说明：
        - 预期容量 (CAPACITY): 1000 万条数据
        - 误判率 (ERROR_RATE): 0.1%
        - 预计内存占用：约 12MB

        注意：这里使用 Redis 原生的 SET 数据结构模拟 Bloom Filter。
        如果需要更好的性能和内存效率，可以使用 RedisBloom 模块。
        """
        if self._bloom_initialized:
            return

        redis_client = await self._get_redis()

        # 检查 Bloom Filter 是否存在
        # 注意：这里使用普通 SET 模拟 Bloom Filter
        # 生产环境建议使用 RedisBloom 模块的 BF.RESERVE 和 BF.ADD 命令
        exists = await redis_client.exists(self.BLOOM_FILTER_KEY)

        if not exists:
            logger.info(
                f"初始化 Bloom Filter: "
                f"容量={settings.BLOOM_FILTER_CAPACITY}, "
                f"误判率={settings.BLOOM_FILTER_ERROR_RATE}"
            )

        self._bloom_initialized = True

    # ==================== URL 哈希去重 ====================

    @staticmethod
    def compute_url_hash(url: str) -> str:
        """
        计算 URL 的 SHA256 哈希值

        URL 规范化处理：
        1. 去除首尾空白
        2. 移除末尾斜杠
        3. 移除 URL 锚点 (#fragment)
        4. 统一为小写（域名部分）

        Args:
            url: 原始 URL

        Returns:
            str: 64 位十六进制哈希字符串
        """
        # URL 规范化
        normalized_url = url.strip().rstrip("/")

        # 移除锚点
        if "#" in normalized_url:
            normalized_url = normalized_url.split("#")[0]

        # 移除常见的追踪参数（可选优化）
        # utm_source, utm_medium, utm_campaign 等
        tracking_params = [
            "utm_source", "utm_medium", "utm_campaign",
            "utm_term", "utm_content", "ref", "source"
        ]
        for param in tracking_params:
            # 简单的正则替换
            normalized_url = re.sub(
                rf"[?&]{param}=[^&]*",
                "",
                normalized_url
            )

        # 清理多余的 ? 或 &
        normalized_url = re.sub(r"\?&", "?", normalized_url)
        normalized_url = re.sub(r"\?$", "", normalized_url)

        # 计算 SHA256 哈希
        return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()

    async def add_to_bloom_filter(self, url_hash: str) -> None:
        """
        将 URL 哈希添加到 Bloom Filter

        Args:
            url_hash: URL 的 SHA256 哈希
        """
        await self._ensure_bloom_filter()
        redis_client = await self._get_redis()

        # 使用 SADD 添加到集合（模拟 Bloom Filter）
        # 生产环境应使用 BF.ADD 命令
        await redis_client.sadd(self.BLOOM_FILTER_KEY, url_hash)

    async def add_many_to_bloom_filter(self, url_hashes: List[str]) -> None:
        """
        批量添加 URL 哈希到 Bloom Filter

        Args:
            url_hashes: URL 哈希列表
        """
        if not url_hashes:
            return

        await self._ensure_bloom_filter()
        redis_client = await self._get_redis()

        # 批量添加
        await redis_client.sadd(self.BLOOM_FILTER_KEY, *url_hashes)
        logger.debug(f"批量添加 {len(url_hashes)} 个哈希到 Bloom Filter")

    async def check_bloom_filter(self, url_hash: str) -> bool:
        """
        检查 URL 哈希是否存在于 Bloom Filter

        注意：Bloom Filter 可能有假阳性（返回 True 但实际不存在），
        但绝不会有假阴性（返回 False 则一定不存在）。

        Args:
            url_hash: URL 的 SHA256 哈希

        Returns:
            bool: True 表示可能存在（需要二次确认），False 表示一定不存在
        """
        await self._ensure_bloom_filter()
        redis_client = await self._get_redis()

        # 使用 SISMEMBER 检查（模拟 Bloom Filter）
        # 生产环境应使用 BF.EXISTS 命令
        return await redis_client.sismember(self.BLOOM_FILTER_KEY, url_hash)

    async def check_many_bloom_filter(self, url_hashes: List[str]) -> Set[str]:
        """
        批量检查 URL 哈希是否存在于 Bloom Filter

        Args:
            url_hashes: URL 哈希列表

        Returns:
            Set[str]: 可能存在的哈希集合
        """
        if not url_hashes:
            return set()

        await self._ensure_bloom_filter()
        redis_client = await self._get_redis()

        # 使用 Pipeline 批量检查
        pipe = redis_client.pipeline()
        for url_hash in url_hashes:
            pipe.sismember(self.BLOOM_FILTER_KEY, url_hash)

        results = await pipe.execute()

        # 返回可能存在的哈希
        return {
            url_hash
            for url_hash, exists in zip(url_hashes, results)
            if exists
        }

    # ==================== SimHash 内容指纹 ====================

    @staticmethod
    def compute_simhash(text: str) -> int:
        """
        计算文本的 SimHash 指纹

        SimHash 是一种局部敏感哈希算法，相似的文本会产生相似的哈希值。
        通过比较汉明距离可以快速检测相似内容。

        Args:
            text: 文本内容

        Returns:
            int: 64 位 SimHash 值
        """
        if not text:
            return 0

        # 清理文本：移除多余空白、标点等
        cleaned_text = re.sub(r"\s+", " ", text.strip())

        # 计算 SimHash
        return Simhash(cleaned_text).value

    @staticmethod
    def hamming_distance(hash1: int, hash2: int) -> int:
        """
        计算两个 SimHash 值的汉明距离

        汉明距离是两个等长字符串在相同位置上不同字符的个数。
        对于 64 位哈希，距离范围是 0-64。

        Args:
            hash1: 第一个 SimHash 值
            hash2: 第二个 SimHash 值

        Returns:
            int: 汉明距离（0-64）
        """
        # 异或操作找出不同的位
        xor = hash1 ^ hash2
        # 统计 1 的个数（即不同的位数）
        return bin(xor).count("1")

    @staticmethod
    def is_similar(hash1: int, hash2: int, threshold: int = 3) -> bool:
        """
        判断两个内容是否相似

        Args:
            hash1: 第一个 SimHash 值
            hash2: 第二个 SimHash 值
            threshold: 汉明距离阈值，默认 3

        Returns:
            bool: 距离 <= 阈值则认为相似
        """
        return DuplicateService.hamming_distance(hash1, hash2) <= threshold

    # ==================== 数据库查询 ====================

    @staticmethod
    async def get_existing_url_hashes(
        db: AsyncSession,
        url_hashes: Set[str],
    ) -> Set[str]:
        """
        从数据库查询已存在的 URL 哈希

        用于处理 Bloom Filter 的假阳性情况。

        Args:
            db: 数据库会话
            url_hashes: 待查询的哈希集合

        Returns:
            Set[str]: 数据库中已存在的哈希集合
        """
        if not url_hashes:
            return set()

        stmt = select(NewsArticle.url_hash).where(
            NewsArticle.url_hash.in_(url_hashes)
        )
        result = await db.execute(stmt)
        existing_hashes = {row[0] for row in result.fetchall()}

        logger.debug(
            f"数据库查询: {len(url_hashes)} 个哈希中有 {len(existing_hashes)} 个已存在"
        )

        return existing_hashes

    # ==================== 综合去重流程 ====================

    async def filter_duplicates(
        self,
        db: AsyncSession,
        articles: List[dict],
    ) -> Tuple[List[dict], List[dict]]:
        """
        过滤重复文章（完整去重流程）

        去重流程：
        1. 提取所有文章的 URL 哈希
        2. 批量查询 Bloom Filter，快速排除一定不存在的
        3. 对 Bloom Filter 返回"可能存在"的，查询数据库二次确认
        4. 分离新文章和重复文章

        Args:
            db: 数据库会话
            articles: 文章字典列表，每个字典必须包含 "url_hash" 字段

        Returns:
            Tuple[List[dict], List[dict]]: (新文章列表, 重复文章列表)
        """
        if not articles:
            return [], []

        # 1. 提取 URL 哈希
        url_hashes = [article["url_hash"] for article in articles]

        # 2. 批量查询 Bloom Filter
        possibly_existing = await self.check_many_bloom_filter(url_hashes)

        # 3. 对"可能存在"的哈希查询数据库确认
        confirmed_existing: Set[str] = set()
        if possibly_existing:
            confirmed_existing = await self.get_existing_url_hashes(
                db, possibly_existing
            )

        # 4. 分离新文章和重复文章
        new_articles = []
        duplicate_articles = []

        for article in articles:
            if article["url_hash"] in confirmed_existing:
                duplicate_articles.append(article)
            else:
                new_articles.append(article)

        # 5. 将新文章的哈希添加到 Bloom Filter
        new_hashes = [a["url_hash"] for a in new_articles]
        await self.add_many_to_bloom_filter(new_hashes)

        logger.info(
            f"去重完成: 总计 {len(articles)} 篇, "
            f"新增 {len(new_articles)} 篇, "
            f"重复 {len(duplicate_articles)} 篇",
            extra={
                "total": len(articles),
                "new": len(new_articles),
                "duplicates": len(duplicate_articles),
            },
        )

        return new_articles, duplicate_articles

    async def close(self) -> None:
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None


# 全局单例实例
_dedup_service: Optional[DuplicateService] = None


def get_dedup_service() -> DuplicateService:
    """
    获取去重服务单例实例

    Returns:
        DuplicateService: 去重服务实例
    """
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = DuplicateService()
    return _dedup_service
