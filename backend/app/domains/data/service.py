"""
Data Pointer Service - 数据指针服务

提供 DataPointer 的 CRUD 操作和可见性控制。
"""

import logging
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.data.models import (
    ArticleAnalysis,
    ArticleContent,
    DataPointer,
    DataVisibility,
)

logger = logging.getLogger(__name__)


class DataPointerService:
    """
    数据指针服务

    管理 DataPointer 的创建、查询和可见性控制。
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_pointer(
        self,
        domain: str,
        domain_table: str,
        domain_id: str,
        created_by: str | None = None,
        tenant_id: int | None = None,
        visibility: DataVisibility = DataVisibility.PRIVATE,
        title: str | None = None,
        url: str | None = None,
        platform: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> DataPointer:
        """
        创建数据指针

        Args:
            domain: 数据域 (news, twitter, telegram)
            domain_table: 域表名
            domain_id: 域内记录 ID
            created_by: 创建者用户 ID
            tenant_id: 租户 ID
            visibility: 可见性
            title: 标题（缓存）
            url: URL（缓存）
            platform: 平台标识（缓存）
            extra_metadata: 额外元数据

        Returns:
            DataPointer: 创建的数据指针
        """
        pointer = DataPointer(
            domain=domain,
            domain_table=domain_table,
            domain_id=domain_id,
            created_by=created_by,
            tenant_id=tenant_id,
            visibility=visibility,
            title=title,
            url=url,
            platform=platform,
            extra_metadata=extra_metadata,
        )
        self.db.add(pointer)
        await self.db.flush()
        return pointer

    async def get_by_id(self, pointer_id: str) -> DataPointer | None:
        """根据 ID 获取数据指针"""
        stmt = select(DataPointer).where(DataPointer.id == pointer_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_reference(
        self,
        domain: str,
        domain_table: str,
        domain_id: str,
    ) -> DataPointer | None:
        """根据域引用获取数据指针"""
        stmt = select(DataPointer).where(
            and_(
                DataPointer.domain == domain,
                DataPointer.domain_table == domain_table,
                DataPointer.domain_id == domain_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        domain: str,
        domain_table: str,
        domain_id: str,
        **kwargs,
    ) -> tuple[DataPointer, bool]:
        """
        获取或创建数据指针

        Returns:
            (DataPointer, created): 数据指针和是否新创建
        """
        pointer = await self.get_by_reference(domain, domain_table, domain_id)
        if pointer:
            return pointer, False

        pointer = await self.create_pointer(
            domain=domain,
            domain_table=domain_table,
            domain_id=domain_id,
            **kwargs,
        )
        return pointer, True

    async def list_visible_to_user(
        self,
        user_id: str,
        tenant_id: int | None = None,
        is_super_admin: bool = False,
        domain: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[DataPointer], int]:
        """
        获取用户可见的数据指针列表

        可见性规则：
        1. 超级管理员可见所有
        2. 普通用户可见：自己创建的 + 租户共享的 + 公开的

        Args:
            user_id: 用户 ID
            tenant_id: 租户 ID
            is_super_admin: 是否超级管理员
            domain: 可选的域过滤
            page: 页码
            per_page: 每页数量

        Returns:
            (列表, 总数)
        """
        # 构建可见性条件
        if is_super_admin:
            visibility_condition = True  # 超级管理员可见所有
        else:
            visibility_conditions = [
                # 自己创建的
                DataPointer.created_by == user_id,
                # 公开的
                DataPointer.visibility == DataVisibility.PUBLIC,
            ]
            # 租户共享的
            if tenant_id:
                visibility_conditions.append(
                    and_(
                        DataPointer.visibility == DataVisibility.TENANT_SHARED,
                        DataPointer.tenant_id == tenant_id,
                    )
                )
            visibility_condition = or_(*visibility_conditions)

        # 构建查询
        stmt = select(DataPointer).where(visibility_condition)

        if domain:
            stmt = stmt.where(DataPointer.domain == domain)

        # 总数
        count_stmt = select(DataPointer.id).where(visibility_condition)
        if domain:
            count_stmt = count_stmt.where(DataPointer.domain == domain)
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.all())

        # 分页
        stmt = stmt.order_by(DataPointer.created_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(stmt)
        pointers = result.scalars().all()

        return list(pointers), total

    async def update_visibility(
        self,
        pointer_id: str,
        visibility: DataVisibility,
        updated_by: str,
    ) -> DataPointer | None:
        """
        更新数据可见性

        Args:
            pointer_id: 数据指针 ID
            visibility: 新的可见性
            updated_by: 操作者用户 ID

        Returns:
            更新后的数据指针或 None
        """
        pointer = await self.get_by_id(pointer_id)
        if not pointer:
            return None

        pointer.visibility = visibility
        await self.db.flush()

        logger.info(
            f"DataPointer visibility updated: {pointer_id} -> {visibility.value}",
            extra={"pointer_id": pointer_id, "visibility": visibility.value, "updated_by": updated_by}
        )

        return pointer

    async def batch_update_visibility(
        self,
        pointer_ids: list[str],
        visibility: DataVisibility,
        updated_by: str,
    ) -> int:
        """
        批量更新可见性

        Args:
            pointer_ids: 数据指针 ID 列表
            visibility: 新的可见性
            updated_by: 操作者用户 ID

        Returns:
            更新的数量
        """
        from sqlalchemy import update

        stmt = (
            update(DataPointer)
            .where(DataPointer.id.in_(pointer_ids))
            .values(visibility=visibility)
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def add_content(
        self,
        pointer_id: str,
        content_text: str | None = None,
        content_html: str | None = None,
        title: str | None = None,
        summary: str | None = None,
        extraction_method: str | None = None,
    ) -> ArticleContent:
        """添加正文提取结果"""
        # 将之前的版本设为非主版本
        from sqlalchemy import update
        await self.db.execute(
            update(ArticleContent)
            .where(ArticleContent.pointer_id == pointer_id)
            .values(is_primary=False)
        )

        # 获取最新版本号
        stmt = select(ArticleContent.version).where(
            ArticleContent.pointer_id == pointer_id
        ).order_by(ArticleContent.version.desc()).limit(1)
        result = await self.db.execute(stmt)
        last_version = result.scalar() or 0

        # 创建新版本
        content = ArticleContent(
            pointer_id=pointer_id,
            title=title,
            content_text=content_text,
            content_html=content_html,
            summary=summary,
            extraction_method=extraction_method,
            word_count=len(content_text) if content_text else 0,
            version=last_version + 1,
            is_primary=True,
        )
        self.db.add(content)

        # 更新指针状态
        await self.db.execute(
            update(DataPointer)
            .where(DataPointer.id == pointer_id)
            .values(has_content=True)
        )

        await self.db.flush()
        return content

    async def add_analysis(
        self,
        pointer_id: str,
        analysis_type: str,
        result: dict[str, Any],
        model_name: str | None = None,
        confidence: float | None = None,
    ) -> ArticleAnalysis:
        """添加分析结果"""
        from sqlalchemy import update

        analysis = ArticleAnalysis(
            pointer_id=pointer_id,
            analysis_type=analysis_type,
            result=result,
            model_name=model_name,
            confidence=confidence,
        )
        self.db.add(analysis)

        # 更新指针状态
        await self.db.execute(
            update(DataPointer)
            .where(DataPointer.id == pointer_id)
            .values(has_analysis=True)
        )

        await self.db.flush()
        return analysis


# 全局服务实例（用于依赖注入）
_service: DataPointerService | None = None


def get_data_pointer_service(db: AsyncSession) -> DataPointerService:
    """获取数据指针服务实例"""
    return DataPointerService(db)
