"""Add missing foreign key constraints for business tables

Revision ID: 20251220_010
Revises: 20251220_009
Create Date: 2025-12-20

修复迁移：
- 为业务表添加缺失的 user_id 外键约束
- 确保数据完整性
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251220_010'
down_revision: Union[str, None] = '20251220_009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加缺失的外键约束"""

    # 需要添加外键的表
    tables_with_fk = [
        'news_sources',
        'news_articles',
        'scraper_runs',
        'social_sessions',
        'account_credentials',
        'proxy_configs',
        'export_tasks',
    ]

    for table in tables_with_fk:
        fk_name = f'fk_{table}_user_id'

        # 先尝试删除可能存在的同名外键
        try:
            op.drop_constraint(fk_name, table, type_='foreignkey')
        except Exception:
            pass  # 约束不存在，忽略

        # 创建新的外键约束
        op.create_foreign_key(
            fk_name,
            table, 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """删除外键约束"""

    tables_with_fk = [
        'news_sources',
        'news_articles',
        'scraper_runs',
        'social_sessions',
        'account_credentials',
        'proxy_configs',
        'export_tasks',
    ]

    for table in tables_with_fk:
        fk_name = f'fk_{table}_user_id'
        try:
            op.drop_constraint(fk_name, table, type_='foreignkey')
        except Exception:
            pass
