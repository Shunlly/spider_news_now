"""
全文搜索 API 端点
Full-Text Search API Endpoints

提供基于 Meilisearch 的全文搜索功能。
遵循宪法 II.B 全文检索要求：响应时间 < 500ms。
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.models.news_article import NewsArticle
from app.schemas.search import (
    FacetCount,
    FacetDistributionResponse,
    IndexStatsResponse,
    IndexTaskResponse,
    SearchHitResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.search_service import SearchService, get_search_service

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


def get_search() -> SearchService:
    """获取搜索服务依赖"""
    return get_search_service()


# =============================================================
# 搜索端点
# =============================================================

@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    hits_per_page: int = Query(20, ge=1, le=100, description="每页结果数"),
    source_key: Optional[str] = Query(None, description="按来源过滤"),
    category: Optional[str] = Query(None, description="按分类过滤"),
    start_date: Optional[datetime] = Query(None, description="时间范围起始"),
    end_date: Optional[datetime] = Query(None, description="时间范围结束"),
    sort_by: Optional[str] = Query(None, description="排序字段，如 published_at:desc"),
    highlight: bool = Query(True, description="是否返回高亮结果"),
    search_service: SearchService = Depends(get_search),
):
    """
    执行全文搜索

    搜索新闻文章，支持：
    - 关键词匹配（标题优先）
    - 按来源、分类、时间范围过滤
    - 自定义排序
    - 结果高亮

    响应时间目标：< 500ms
    """
    try:
        result = await search_service.search(
            query=q,
            page=page,
            hits_per_page=hits_per_page,
            source_key=source_key,
            category=category,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            highlight=highlight,
        )

        # 转换搜索结果
        hits = []
        for hit in result["hits"]:
            # 提取高亮内容
            formatted = hit.get("_formatted", {})

            hits.append(SearchHitResponse(
                id=hit["id"],
                title=hit["title"],
                url=hit["url"],
                source_key=hit["source_key"],
                category=hit.get("category"),
                published_at=_timestamp_to_datetime(hit.get("published_at")),
                title_highlighted=formatted.get("title") if highlight else None,
                content_highlighted=formatted.get("content") if highlight else None,
            ))

        return SearchResponse(
            hits=hits,
            query=result["query"],
            total_hits=result["total_hits"],
            page=result["page"],
            hits_per_page=result["hits_per_page"],
            total_pages=result["total_pages"],
            processing_time_ms=result["processing_time_ms"],
        )

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.get("/facets", response_model=SearchResponse)
async def search_with_facets(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    hits_per_page: int = Query(20, ge=1, le=100, description="每页结果数"),
    source_key: Optional[str] = Query(None, description="按来源过滤"),
    category: Optional[str] = Query(None, description="按分类过滤"),
    start_date: Optional[datetime] = Query(None, description="时间范围起始"),
    end_date: Optional[datetime] = Query(None, description="时间范围结束"),
    search_service: SearchService = Depends(get_search),
):
    """
    带分面统计的搜索

    返回搜索结果和各维度的分布统计，便于前端实现筛选功能。
    """
    try:
        result, facet_dist = await search_service.search_with_facets(
            query=q,
            page=page,
            hits_per_page=hits_per_page,
            source_key=source_key,
            category=category,
            start_date=start_date,
            end_date=end_date,
        )

        # 转换搜索结果
        hits = []
        for hit in result["hits"]:
            formatted = hit.get("_formatted", {})
            hits.append(SearchHitResponse(
                id=hit["id"],
                title=hit["title"],
                url=hit["url"],
                source_key=hit["source_key"],
                category=hit.get("category"),
                published_at=_timestamp_to_datetime(hit.get("published_at")),
                title_highlighted=formatted.get("title"),
                content_highlighted=formatted.get("content"),
            ))

        # 转换分面统计
        facets = FacetDistributionResponse(
            source_key=[
                FacetCount(value=k, count=v)
                for k, v in facet_dist["source_key"].items()
            ],
            category=[
                FacetCount(value=k, count=v)
                for k, v in facet_dist["category"].items()
            ],
        )

        return SearchResponse(
            hits=hits,
            query=result["query"],
            total_hits=result["total_hits"],
            page=result["page"],
            hits_per_page=result["hits_per_page"],
            total_pages=result["total_pages"],
            processing_time_ms=result["processing_time_ms"],
            facets=facets,
        )

    except Exception as e:
        logger.error(f"分面搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


# =============================================================
# 索引管理端点（管理员功能）
# =============================================================

@router.get("/index/stats", response_model=IndexStatsResponse)
async def get_index_stats(
    search_service: SearchService = Depends(get_search),
):
    """
    获取索引统计信息

    返回文档数量、索引状态等信息。
    """
    try:
        stats = await search_service.get_index_stats()

        return IndexStatsResponse(
            index_name=search_service.INDEX_NAME,
            number_of_documents=stats["number_of_documents"],
            is_indexing=stats["is_indexing"],
            field_distribution=stats.get("field_distribution", {}),
        )

    except Exception as e:
        logger.error(f"获取索引统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.post("/index/clear", response_model=IndexTaskResponse)
async def clear_index(
    search_service: SearchService = Depends(get_search),
):
    """
    清空搜索索引

    警告：此操作不可逆！仅用于重建索引前的清理。
    """
    try:
        task_id = await search_service.clear_index()

        return IndexTaskResponse(
            task_id=task_id,
            status="enqueued",
            message="索引清空任务已提交",
        )

    except Exception as e:
        logger.error(f"清空索引失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索服务错误: {str(e)}")


@router.post("/index/rebuild", response_model=IndexTaskResponse)
async def rebuild_index(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    search_service: SearchService = Depends(get_search),
):
    """
    重建搜索索引

    将数据库中所有文章重新索引到 Meilisearch。
    此操作在后台执行，可能需要一段时间完成。
    """
    # 在后台执行索引重建
    background_tasks.add_task(_rebuild_index_background, db, search_service)

    return IndexTaskResponse(
        task_id="rebuild",
        status="started",
        message="索引重建任务已在后台启动",
    )


async def _rebuild_index_background(db: AsyncSession, search_service: SearchService):
    """后台重建索引"""
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        try:
            # 获取所有文章
            stmt = select(NewsArticle)
            result = await session.execute(stmt)
            articles = result.scalars().all()

            logger.info(f"开始重建索引，共 {len(articles)} 篇文章")

            # 准备文档数据
            documents = []
            for article in articles:
                documents.append({
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "source_key": article.source_key,
                    "category": article.category,
                    "content": article.content_text,
                    "published_at": article.published_at,
                    "created_at": article.created_at,
                })

            # 重建索引
            if documents:
                task_id = await search_service.rebuild_index(documents)
                logger.info(f"索引重建完成，task_id: {task_id}")
            else:
                logger.warning("没有文章需要索引")

        except Exception as e:
            logger.error(f"索引重建失败: {e}", exc_info=True)


# =============================================================
# 辅助函数
# =============================================================

def _timestamp_to_datetime(timestamp: Optional[int]) -> datetime:
    """将 Unix 时间戳转换为 datetime"""
    if timestamp is None:
        return datetime.now()
    return datetime.fromtimestamp(timestamp)
