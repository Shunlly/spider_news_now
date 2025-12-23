"""
User Data Service - 用户数据服务

提供用户数据关系的 CRUD 操作。
"""

import logging
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.user_data.models import UserDataRelation

logger = logging.getLogger(__name__)


class UserDataService:
    """用户数据关系服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_relation(
        self,
        user_id: str,
        pointer_id: str,
    ) -> tuple[UserDataRelation, bool]:
        """获取或创建用户数据关系"""
        stmt = select(UserDataRelation).where(
            and_(
                UserDataRelation.user_id == user_id,
                UserDataRelation.pointer_id == pointer_id,
            )
        )
        result = await self.db.execute(stmt)
        relation = result.scalar_one_or_none()

        if relation:
            return relation, False

        relation = UserDataRelation(
            user_id=user_id,
            pointer_id=pointer_id,
        )
        self.db.add(relation)
        await self.db.flush()
        return relation, True

    async def toggle_favorite(
        self,
        user_id: str,
        pointer_id: str,
    ) -> bool:
        """切换收藏状态"""
        relation, _ = await self.get_or_create_relation(user_id, pointer_id)
        relation.is_favorited = not relation.is_favorited
        await self.db.flush()
        return relation.is_favorited

    async def toggle_bookmark(
        self,
        user_id: str,
        pointer_id: str,
    ) -> bool:
        """切换书签状态"""
        relation, _ = await self.get_or_create_relation(user_id, pointer_id)
        relation.is_bookmarked = not relation.is_bookmarked
        await self.db.flush()
        return relation.is_bookmarked

    async def mark_as_read(
        self,
        user_id: str,
        pointer_id: str,
    ) -> None:
        """标记为已读"""
        relation, _ = await self.get_or_create_relation(user_id, pointer_id)
        relation.is_read = True
        relation.read_at = datetime.utcnow()
        await self.db.flush()

    async def add_tag(
        self,
        user_id: str,
        pointer_id: str,
        tag: str,
    ) -> list[str]:
        """添加标签"""
        relation, _ = await self.get_or_create_relation(user_id, pointer_id)
        tags = relation.user_tags or []
        if tag not in tags:
            tags.append(tag)
            relation.user_tags = tags
            await self.db.flush()
        return tags

    async def remove_tag(
        self,
        user_id: str,
        pointer_id: str,
        tag: str,
    ) -> list[str]:
        """移除标签"""
        relation, _ = await self.get_or_create_relation(user_id, pointer_id)
        tags = relation.user_tags or []
        if tag in tags:
            tags.remove(tag)
            relation.user_tags = tags
            await self.db.flush()
        return tags

    async def update_notes(
        self,
        user_id: str,
        pointer_id: str,
        notes: str,
    ) -> None:
        """更新笔记"""
        relation, _ = await self.get_or_create_relation(user_id, pointer_id)
        relation.user_notes = notes
        await self.db.flush()

    async def get_user_favorites(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[UserDataRelation], int]:
        """获取用户收藏列表"""
        stmt = select(UserDataRelation).where(
            and_(
                UserDataRelation.user_id == user_id,
                UserDataRelation.is_favorited == True,  # noqa: E712
            )
        ).order_by(UserDataRelation.updated_at.desc())

        # 总数
        count_stmt = select(UserDataRelation.id).where(
            and_(
                UserDataRelation.user_id == user_id,
                UserDataRelation.is_favorited == True,  # noqa: E712
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.all())

        # 分页
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(stmt)
        relations = result.scalars().all()

        return list(relations), total

    async def get_user_bookmarks(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[UserDataRelation], int]:
        """获取用户书签列表"""
        stmt = select(UserDataRelation).where(
            and_(
                UserDataRelation.user_id == user_id,
                UserDataRelation.is_bookmarked == True,  # noqa: E712
            )
        ).order_by(UserDataRelation.updated_at.desc())

        # 总数
        count_stmt = select(UserDataRelation.id).where(
            and_(
                UserDataRelation.user_id == user_id,
                UserDataRelation.is_bookmarked == True,  # noqa: E712
            )
        )
        count_result = await self.db.execute(count_stmt)
        total = len(count_result.all())

        # 分页
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(stmt)
        relations = result.scalars().all()

        return list(relations), total


def get_user_data_service(db: AsyncSession) -> UserDataService:
    """获取用户数据服务实例"""
    return UserDataService(db)
