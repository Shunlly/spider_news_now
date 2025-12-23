"""
Meilisearch 索引 Celery 任务
Search Indexing Celery Tasks

遵循宪法要求：
- 异步批量索引文档到 Meilisearch
- 支持任务失败自动重试
- 提供索引重建任务
"""

import asyncio
from typing import Any

from celery import shared_task
from celery.utils.log import get_task_logger

from app.core.config import settings

logger = get_task_logger(__name__)


def run_async(coro):
    """在 Celery Worker 中运行异步协程"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 60秒后重试
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 最大重试延迟10分钟
)
def index_documents_task(self, documents: list[dict[str, Any]]) -> dict:
    """
    异步批量索引文档到 Meilisearch

    Args:
        documents: 要索引的文档列表

    Returns:
        dict: 任务结果
    """
    async def _index():
        from app.services.search_service import get_search_service

        search_service = get_search_service()
        task_uid = await search_service.index_documents(documents)
        return task_uid

    try:
        if not documents:
            logger.info("No documents to index")
            return {"status": "skipped", "count": 0}

        logger.info(f"Indexing {len(documents)} documents to Meilisearch")
        task_uid = run_async(_index())

        logger.info(f"Indexed {len(documents)} documents, task_uid: {task_uid}")
        return {
            "status": "success",
            "count": len(documents),
            "task_uid": task_uid,
        }

    except Exception as e:
        logger.error(f"Failed to index documents: {e}")
        raise self.retry(exc=e) from e


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def delete_documents_task(self, document_ids: list[int]) -> dict:
    """
    异步批量删除文档

    Args:
        document_ids: 要删除的文档 ID 列表

    Returns:
        dict: 任务结果
    """
    async def _delete():
        from app.services.search_service import get_search_service

        search_service = get_search_service()
        task_uid = await search_service.delete_documents(document_ids)
        return task_uid

    try:
        if not document_ids:
            return {"status": "skipped", "count": 0}

        logger.info(f"Deleting {len(document_ids)} documents from Meilisearch")
        task_uid = run_async(_delete())

        logger.info(f"Deleted {len(document_ids)} documents, task_uid: {task_uid}")
        return {
            "status": "success",
            "count": len(document_ids),
            "task_uid": task_uid,
        }

    except Exception as e:
        logger.error(f"Failed to delete documents: {e}")
        raise self.retry(exc=e) from e


@shared_task(bind=True, max_retries=1, time_limit=3600)
def reindex_all_task(self, user_id: str | None = None, tenant_id: int | None = None) -> dict:
    """
    重建索引任务

    可选择性地只重建特定用户或租户的索引。

    Args:
        user_id: 可选，仅重建指定用户的文档
        tenant_id: 可选，仅重建指定租户的文档

    Returns:
        dict: 任务结果
    """
    async def _reindex():
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.db.session import async_session_maker
        from app.models.news_article import NewsArticle
        from app.services.search_service import get_search_service

        search_service = get_search_service()

        async with async_session_maker() as session:
            # 构建查询
            stmt = select(NewsArticle).options(selectinload(NewsArticle.owner))

            if user_id:
                stmt = stmt.where(NewsArticle.user_id == user_id)

            result = await session.execute(stmt)
            articles = result.scalars().all()

            logger.info(f"Found {len(articles)} articles to reindex")

            if not articles:
                return {"status": "skipped", "count": 0}

            # 准备文档数据（包含多租户信息）
            documents = []
            for article in articles:
                # 如果指定了 tenant_id，过滤不匹配的文章
                if tenant_id and article.owner and article.owner.tenant_id != tenant_id:
                    continue

                documents.append({
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "source_key": article.source_key,
                    "category": article.category,
                    "content": article.content_text[:settings.MEILISEARCH_CONTENT_MAX_LENGTH] if article.content_text else None,
                    "published_at": article.published_at,
                    "created_at": article.created_at,
                    "user_id": article.user_id,
                    "tenant_id": str(article.owner.tenant_id) if article.owner and article.owner.tenant_id else None,
                })

            # 分批索引
            batch_size = settings.MEILISEARCH_BATCH_SIZE
            indexed_count = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                task_uid = await search_service.index_documents(batch)
                indexed_count += len(batch)
                logger.info(f"Indexed batch {i // batch_size + 1}, count: {len(batch)}, task_uid: {task_uid}")

            return {
                "status": "success",
                "count": indexed_count,
                "total_articles": len(articles),
            }

    try:
        logger.info(f"Starting reindex task, user_id: {user_id}, tenant_id: {tenant_id}")
        result = run_async(_reindex())
        logger.info(f"Reindex completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        raise


def index_documents_async(documents: list[dict[str, Any]]) -> str | None:
    """
    异步索引文档的便捷函数

    根据配置决定是同步索引还是发送到 Celery 队列。

    Args:
        documents: 要索引的文档列表

    Returns:
        str | None: 同步模式返回 task_uid，异步模式返回 Celery task id
    """
    if not documents:
        return None

    if settings.MEILISEARCH_ASYNC_INDEXING:
        # 异步模式：发送到 Celery 队列
        task = index_documents_task.delay(documents)
        logger.info(f"Queued {len(documents)} documents for indexing, celery_task_id: {task.id}")
        return task.id
    else:
        # 同步模式：直接索引
        async def _sync_index():
            from app.services.search_service import get_search_service
            search_service = get_search_service()
            return await search_service.index_documents(documents)

        return run_async(_sync_index())


def delete_documents_async(document_ids: list[int]) -> str | None:
    """
    异步删除文档的便捷函数

    Args:
        document_ids: 要删除的文档 ID 列表

    Returns:
        str | None: 同步模式返回 task_uid，异步模式返回 Celery task id
    """
    if not document_ids:
        return None

    if settings.MEILISEARCH_ASYNC_INDEXING:
        task = delete_documents_task.delay(document_ids)
        logger.info(f"Queued {len(document_ids)} documents for deletion, celery_task_id: {task.id}")
        return task.id
    else:
        async def _sync_delete():
            from app.services.search_service import get_search_service
            search_service = get_search_service()
            return await search_service.delete_documents(document_ids)

        return run_async(_sync_delete())
