"""
正文解析服务
ContentParserService - 后台异步解析文章正文

两阶段抓取策略：
1. 第一阶段：快速抓取列表页，保存基础信息（标题、URL等）
2. 第二阶段：后台任务异步解析正文内容
"""

import asyncio
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.news_article import NewsArticle
from app.scrapers.base import BaseScraper
from app.services.storage_service import get_storage_service
from app.services.search_service import get_search_service

logger = get_logger(__name__)

# 最大重试次数
MAX_RETRY_COUNT = 3
# 每批处理数量
BATCH_SIZE = 10
# 并发数
CONCURRENCY = 3


class ContentParserService:
    """
    正文解析服务

    负责后台异步解析文章正文内容，支持：
    - 批量处理待解析文章
    - 重试失败的文章
    - 并发控制
    - 存储到 RustFS
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage_service = get_storage_service()
        self.search_service = get_search_service()
        self.semaphore = asyncio.Semaphore(CONCURRENCY)

    async def get_pending_articles(self, limit: int = BATCH_SIZE) -> list[NewsArticle]:
        """
        获取待解析的文章

        Args:
            limit: 返回数量限制

        Returns:
            待解析的文章列表
        """
        stmt = (
            select(NewsArticle)
            .where(
                NewsArticle.content_status.in_(["pending", "failed"]),
                NewsArticle.content_retry_count < MAX_RETRY_COUNT,
            )
            .order_by(NewsArticle.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def parse_article_content(self, article: NewsArticle) -> bool:
        """
        解析单篇文章的正文内容

        Args:
            article: 文章对象

        Returns:
            是否成功
        """

        async with self.semaphore:
            try:
                # 标记为解析中
                await self.db.execute(
                    update(NewsArticle)
                    .where(NewsArticle.id == article.id)
                    .values(content_status="parsing")
                )
                await self.db.commit()

                # 根据来源选择合适的解析器
                scraper = self._get_scraper_for_source(article.source_key)

                # 解析正文
                content = await scraper.fetch_content(article.url)

                if content and len(content.strip()) > 50:
                    # 生成存储路径
                    date_str = datetime.now().strftime("%Y/%m/%d")
                    file_path = f"articles/{article.source_key}/{date_str}/{article.url_hash}.html"

                    # 上传到 RustFS
                    try:
                        await self.storage_service.upload(
                            file_path,
                            content.encode("utf-8"),
                            content_type="text/html; charset=utf-8",
                        )

                        # 提取纯文本用于搜索
                        content_text = self._extract_plain_text(content)
                        content_hash = BaseScraper._generate_hash(content)

                        # 更新文章
                        await self.db.execute(
                            update(NewsArticle)
                            .where(NewsArticle.id == article.id)
                            .values(
                                content_url=file_path,
                                content_text=content_text,
                                content_hash=content_hash,
                                content_status="completed",
                            )
                        )
                        await self.db.commit()

                        # 更新搜索索引
                        await self._update_search_index(article, content_text)

                        logger.info(f"Successfully parsed content for article {article.id}: {article.title[:30]}...")
                        return True

                    except Exception as e:
                        logger.warning(f"Failed to upload content to storage: {e}")
                        # 存储失败，仍然保存正文到数据库
                        content_text = self._extract_plain_text(content)
                        content_hash = BaseScraper._generate_hash(content)

                        await self.db.execute(
                            update(NewsArticle)
                            .where(NewsArticle.id == article.id)
                            .values(
                                content_text=content_text,
                                content_hash=content_hash,
                                content_status="completed",
                            )
                        )
                        await self.db.commit()
                        return True

                else:
                    # 正文解析失败
                    await self._mark_failed(article)
                    return False

            except Exception as e:
                logger.error(f"Failed to parse content for article {article.id}: {e}")
                await self._mark_failed(article)
                return False

    async def _mark_failed(self, article: NewsArticle):
        """标记文章解析失败"""
        await self.db.execute(
            update(NewsArticle)
            .where(NewsArticle.id == article.id)
            .values(
                content_status="failed",
                content_retry_count=article.content_retry_count + 1,
            )
        )
        await self.db.commit()

    def _get_scraper_for_source(self, source_key: str) -> BaseScraper:
        """
        根据来源获取对应的爬虫实例

        Args:
            source_key: 来源标识

        Returns:
            爬虫实例
        """
        # 动态导入爬虫类
        import importlib

        try:
            module_name = f"app.scrapers.{source_key}_scraper"
            module = importlib.import_module(module_name)

            # 特殊处理类名
            class_name_mappings = {"qq": "QQScraper"}
            class_name = class_name_mappings.get(source_key, f"{source_key.capitalize()}Scraper")

            scraper_class = getattr(module, class_name)
            return scraper_class()
        except (ImportError, AttributeError):
            # 使用通用解析器
            return GenericContentParser(source_key)

    @staticmethod
    def _extract_plain_text(html_content: str) -> str:
        """从 HTML 中提取纯文本"""
        import re

        text = re.sub(r"<[^>]+>", " ", html_content)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:10000]  # 限制长度

    async def _update_search_index(self, article: NewsArticle, content_text: str):
        """更新搜索索引"""
        try:
            doc = {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source_key": article.source_key,
                "category": article.category,
                "content": content_text,
                "published_at": article.published_at,
                "created_at": article.created_at,
            }
            await self.search_service.index_documents([doc])
        except Exception as e:
            logger.warning(f"Failed to update search index for article {article.id}: {e}")

    async def run_batch(self, limit: int = BATCH_SIZE) -> dict:
        """
        执行一批正文解析任务

        Args:
            limit: 处理数量限制

        Returns:
            处理结果统计
        """
        articles = await self.get_pending_articles(limit)

        if not articles:
            logger.info("No pending articles to parse")
            return {"total": 0, "success": 0, "failed": 0}

        logger.info(f"Starting to parse {len(articles)} articles")

        # 并发解析
        tasks = [self.parse_article_content(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        failed_count = len(results) - success_count

        logger.info(f"Batch parsing completed: {success_count} success, {failed_count} failed")

        return {
            "total": len(articles),
            "success": success_count,
            "failed": failed_count,
        }


class GenericContentParser(BaseScraper):
    """通用正文解析器"""

    def __init__(self, source_key: str):
        super().__init__(source_key=source_key, display_name=f"Generic-{source_key}")

    async def scrape(self):
        """不实现抓取，只用于正文解析"""
        return []


async def run_content_parser(db: AsyncSession, limit: int = BATCH_SIZE) -> dict:
    """
    运行正文解析任务

    Args:
        db: 数据库会话
        limit: 处理数量限制

    Returns:
        处理结果统计
    """
    service = ContentParserService(db)
    return await service.run_batch(limit)
