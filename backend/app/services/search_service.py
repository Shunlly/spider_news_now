"""
Meilisearch 全文搜索服务
Meilisearch Full-Text Search Service

遵循宪法 II.B 全文检索要求：
- 支持中文分词搜索
- 按时间/来源/分类过滤
- 响应时间 < 500ms

搜索流程：
1. 文章入库时同步索引到 Meilisearch
2. 搜索时通过 Meilisearch 获取匹配文档 ID
3. 支持高亮、分面搜索、排序等高级功能
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.errors import MeilisearchApiError
from meilisearch_python_sdk.models.settings import (
    Faceting,
    MeilisearchSettings,
    Pagination,
    TypoTolerance,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class SearchHit(TypedDict):
    """搜索结果条目类型定义"""
    id: int
    title: str
    url: str
    source_key: str
    category: Optional[str]
    published_at: str
    _formatted: Optional[Dict[str, Any]]  # 高亮格式化字段


class SearchResult(TypedDict):
    """搜索响应类型定义"""
    hits: List[SearchHit]
    query: str
    processing_time_ms: int
    total_hits: int
    page: int
    hits_per_page: int
    total_pages: int


class FacetDistribution(TypedDict):
    """分面统计类型定义"""
    source_key: Dict[str, int]
    category: Dict[str, int]


class SearchService:
    """
    Meilisearch 全文搜索服务

    提供文章索引管理和全文搜索能力。
    支持中文分词、高亮显示、分面过滤等功能。
    """

    # 索引名称
    INDEX_NAME = "news_articles"

    # 可搜索字段（按优先级排序）
    SEARCHABLE_ATTRIBUTES = [
        "title",      # 标题最高优先级
        "content",    # 正文内容
        "source_key", # 来源
        "category",   # 分类
    ]

    # 可过滤字段
    FILTERABLE_ATTRIBUTES = [
        "source_key",
        "category",
        "published_at",
    ]

    # 可排序字段
    SORTABLE_ATTRIBUTES = [
        "published_at",
        "created_at",
    ]

    # 用于分面搜索的字段
    FACETING_ATTRIBUTES = [
        "source_key",
        "category",
    ]

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        初始化搜索服务

        Args:
            url: Meilisearch 服务地址
            api_key: API 密钥
        """
        self.url = url or settings.MEILISEARCH_URL
        self.api_key = api_key or settings.MEILISEARCH_API_KEY
        self._client: Optional[AsyncClient] = None
        self._index_initialized = False

    async def _get_client(self) -> AsyncClient:
        """
        获取 Meilisearch 异步客户端（懒加载）

        使用单例模式避免重复创建连接。
        """
        if self._client is None:
            self._client = AsyncClient(
                url=self.url,
                api_key=self.api_key if self.api_key else None,
            )
        return self._client

    async def _ensure_index(self) -> None:
        """
        确保索引已创建并配置正确

        索引配置说明：
        - 主键：id (文章数据库主键)
        - 分词：使用 Meilisearch 内置中文分词
        - 排序：默认按发布时间降序
        """
        if self._index_initialized:
            return

        client = await self._get_client()

        try:
            # 尝试获取索引，不存在则创建
            try:
                await client.get_index(self.INDEX_NAME)
                logger.debug(f"索引已存在: {self.INDEX_NAME}")
            except MeilisearchApiError as e:
                if "index_not_found" in str(e):
                    # 创建索引，指定主键为 id
                    task = await client.create_index(
                        uid=self.INDEX_NAME,
                        primary_key="id",
                    )
                    task_uid = getattr(task, 'task_uid', None) or getattr(task, 'uid', 'unknown')
                    logger.info(f"创建索引: {self.INDEX_NAME}, task_uid={task_uid}")
                else:
                    raise

            # 配置索引设置
            index = client.index(self.INDEX_NAME)

            # 构建索引设置
            index_settings = MeilisearchSettings(
                searchable_attributes=self.SEARCHABLE_ATTRIBUTES,
                filterable_attributes=self.FILTERABLE_ATTRIBUTES,
                sortable_attributes=self.SORTABLE_ATTRIBUTES,
                # 排名规则：相关性 > 时间
                ranking_rules=[
                    "words",
                    "typo",
                    "proximity",
                    "attribute",
                    "sort",
                    "exactness",
                    "published_at:desc",  # 新文章优先
                ],
                # 分面配置
                faceting=Faceting(max_values_per_facet=100),
                # 分页配置
                pagination=Pagination(max_total_hits=10000),
                # 错字容忍配置
                typo_tolerance=TypoTolerance(
                    enabled=True,
                    min_word_size_for_typos={"oneTypo": 4, "twoTypos": 8},
                ),
            )

            settings_task = await index.update_settings(index_settings)

            # 等待设置任务完成
            settings_task_uid = getattr(settings_task, 'task_uid', None) or getattr(settings_task, 'uid', None)
            if settings_task_uid:
                try:
                    await client.wait_for_task(settings_task_uid, timeout_in_ms=30000)
                except Exception as e:
                    logger.warning(f"等待索引设置任务超时，继续运行: {e}")

            logger.info(f"索引配置更新完成: {self.INDEX_NAME}")

            self._index_initialized = True

        except Exception as e:
            logger.error(f"初始化索引失败: {e}")
            raise

    # ==================== 文档索引操作 ====================

    async def index_document(self, document: Dict[str, Any]) -> str:
        """
        索引单个文档

        Args:
            document: 文档数据，必须包含 id 字段

        Returns:
            str: 任务 ID
        """
        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        # 确保日期字段格式正确（Meilisearch 需要 ISO 8601 格式或时间戳）
        doc = self._prepare_document(document)

        task = await index.add_documents([doc])
        task_uid = getattr(task, 'task_uid', None) or getattr(task, 'uid', 'unknown')
        logger.debug(f"文档索引完成: id={document.get('id')}, task_uid={task_uid}")
        return str(task_uid)

    async def index_documents(self, documents: List[Dict[str, Any]]) -> str:
        """
        批量索引文档

        Args:
            documents: 文档列表

        Returns:
            str: 任务 ID
        """
        if not documents:
            return ""

        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        # 预处理所有文档
        docs = [self._prepare_document(doc) for doc in documents]

        task = await index.add_documents(docs)
        task_uid = getattr(task, 'task_uid', None) or getattr(task, 'uid', 'unknown')
        logger.info(f"批量索引 {len(docs)} 个文档, task_uid={task_uid}")
        return str(task_uid)

    async def delete_document(self, document_id: int) -> str:
        """
        删除单个文档

        Args:
            document_id: 文档 ID

        Returns:
            str: 任务 ID
        """
        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        task = await index.delete_document(str(document_id))
        task_uid = getattr(task, 'task_uid', None) or getattr(task, 'uid', 'unknown')
        logger.debug(f"文档删除: id={document_id}, task_uid={task_uid}")
        return str(task_uid)

    async def delete_documents(self, document_ids: List[int]) -> str:
        """
        批量删除文档

        Args:
            document_ids: 文档 ID 列表

        Returns:
            str: 任务 ID
        """
        if not document_ids:
            return ""

        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        task = await index.delete_documents([str(id) for id in document_ids])
        task_uid = getattr(task, 'task_uid', None) or getattr(task, 'uid', 'unknown')
        logger.info(f"批量删除 {len(document_ids)} 个文档, task_uid={task_uid}")
        return str(task_uid)

    async def update_document(self, document: Dict[str, Any]) -> str:
        """
        更新文档（部分更新）

        Meilisearch 的 add_documents 在文档 ID 相同时会自动更新。

        Args:
            document: 文档数据，必须包含 id 字段

        Returns:
            str: 任务 ID
        """
        return await self.index_document(document)

    # ==================== 搜索操作 ====================

    async def search(
        self,
        query: str,
        *,
        page: int = 1,
        hits_per_page: int = 20,
        source_key: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: Optional[str] = None,
        highlight: bool = True,
    ) -> SearchResult:
        """
        执行全文搜索

        搜索策略：
        1. 对 query 进行全文匹配（标题优先）
        2. 应用过滤条件（来源、分类、时间范围）
        3. 按指定字段排序（默认按发布时间降序）
        4. 返回高亮结果

        Args:
            query: 搜索关键词
            page: 页码（从 1 开始）
            hits_per_page: 每页结果数
            source_key: 按来源过滤
            category: 按分类过滤
            start_date: 时间范围起始
            end_date: 时间范围结束
            sort_by: 排序字段，如 "published_at:desc"
            highlight: 是否返回高亮结果

        Returns:
            SearchResult: 搜索结果
        """
        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        # 构建过滤条件
        filters = self._build_filter(
            source_key=source_key,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )

        # 构建排序规则
        sort_rules = []
        if sort_by:
            sort_rules.append(sort_by)
        else:
            sort_rules.append("published_at:desc")  # 默认按时间降序

        # 执行搜索
        result = await index.search(
            query,
            offset=(page - 1) * hits_per_page,
            limit=hits_per_page,
            filter=filters if filters else None,
            sort=sort_rules if sort_rules else None,
            attributes_to_highlight=["title", "content"] if highlight else None,
            highlight_pre_tag="<mark>",
            highlight_post_tag="</mark>",
        )

        # 计算总页数
        total_hits = result.estimated_total_hits or 0
        total_pages = (total_hits + hits_per_page - 1) // hits_per_page if total_hits > 0 else 0

        return SearchResult(
            hits=result.hits,
            query=query,
            processing_time_ms=result.processing_time_ms,
            total_hits=total_hits,
            page=page,
            hits_per_page=hits_per_page,
            total_pages=total_pages,
        )

    async def search_with_facets(
        self,
        query: str,
        *,
        page: int = 1,
        hits_per_page: int = 20,
        facets: Optional[List[str]] = None,
        **kwargs,
    ) -> tuple[SearchResult, FacetDistribution]:
        """
        带分面统计的搜索

        分面搜索允许用户看到各分类下的文档数量分布，
        便于进行细粒度筛选。

        Args:
            query: 搜索关键词
            page: 页码
            hits_per_page: 每页结果数
            facets: 要统计的分面字段列表
            **kwargs: 其他搜索参数

        Returns:
            tuple: (搜索结果, 分面统计)
        """
        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        # 默认分面字段
        if facets is None:
            facets = self.FACETING_ATTRIBUTES

        # 构建过滤条件
        filters = self._build_filter(
            source_key=kwargs.get("source_key"),
            category=kwargs.get("category"),
            start_date=kwargs.get("start_date"),
            end_date=kwargs.get("end_date"),
        )

        # 执行搜索
        result = await index.search(
            query,
            offset=(page - 1) * hits_per_page,
            limit=hits_per_page,
            filter=filters if filters else None,
            facets=facets,
            attributes_to_highlight=["title", "content"],
            highlight_pre_tag="<mark>",
            highlight_post_tag="</mark>",
        )

        # 计算总页数
        total_hits = result.estimated_total_hits or 0
        total_pages = (total_hits + hits_per_page - 1) // hits_per_page if total_hits > 0 else 0

        search_result = SearchResult(
            hits=result.hits,
            query=query,
            processing_time_ms=result.processing_time_ms,
            total_hits=total_hits,
            page=page,
            hits_per_page=hits_per_page,
            total_pages=total_pages,
        )

        # 提取分面统计
        facet_distribution = FacetDistribution(
            source_key=result.facet_distribution.get("source_key", {}) if result.facet_distribution else {},
            category=result.facet_distribution.get("category", {}) if result.facet_distribution else {},
        )

        return search_result, facet_distribution

    # ==================== 辅助方法 ====================

    def _prepare_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理文档数据

        将 datetime 对象转换为 Unix 时间戳（Meilisearch 推荐格式）。
        """
        doc = document.copy()

        # 转换日期字段为时间戳
        date_fields = ["published_at", "created_at", "updated_at", "scraped_at"]
        for field in date_fields:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = int(doc[field].timestamp())

        return doc

    def _build_filter(
        self,
        source_key: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[str]:
        """
        构建 Meilisearch 过滤表达式

        Meilisearch 使用类 SQL 的过滤语法。
        """
        conditions = []

        if source_key:
            conditions.append(f'source_key = "{source_key}"')

        if category:
            conditions.append(f'category = "{category}"')

        if start_date:
            timestamp = int(start_date.timestamp())
            conditions.append(f"published_at >= {timestamp}")

        if end_date:
            timestamp = int(end_date.timestamp())
            conditions.append(f"published_at <= {timestamp}")

        if conditions:
            return " AND ".join(conditions)

        return None

    # ==================== 索引管理 ====================

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            Dict: 包含文档数量、索引大小等信息
        """
        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        stats = await index.get_stats()
        return {
            "number_of_documents": stats.number_of_documents,
            "is_indexing": stats.is_indexing,
            "field_distribution": stats.field_distribution,
        }

    async def clear_index(self) -> str:
        """
        清空索引中的所有文档

        警告：此操作不可逆！

        Returns:
            str: 任务 ID
        """
        await self._ensure_index()
        client = await self._get_client()
        index = client.index(self.INDEX_NAME)

        task = await index.delete_all_documents()
        task_uid = getattr(task, 'task_uid', None) or getattr(task, 'uid', 'unknown')
        logger.warning(f"索引已清空: {self.INDEX_NAME}, task_uid={task_uid}")
        return str(task_uid)

    async def rebuild_index(self, documents: List[Dict[str, Any]]) -> str:
        """
        重建索引

        先清空索引，再批量导入所有文档。

        Args:
            documents: 所有文档列表

        Returns:
            str: 任务 ID
        """
        await self.clear_index()
        return await self.index_documents(documents)

    async def close(self) -> None:
        """关闭客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局单例实例
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """
    获取搜索服务单例实例

    Returns:
        SearchService: 搜索服务实例
    """
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
