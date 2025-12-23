"""Migrate historical data - assign NULL user_id to admin

Revision ID: 20251220_009
Revises: 20251218_008
Create Date: 2025-12-20

历史数据迁移：
- 将所有 user_id 为 NULL 的记录分配给管理员用户
- 涉及表: news_sources, news_articles, scraper_runs, export_tasks,
         social_sessions, proxy_configs, account_credentials
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251220_009'
down_revision: Union[str, None] = '20251218_008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 管理员用户 ID
ADMIN_USER_ID = '00000000-0000-0000-0000-000000000001'


def upgrade() -> None:
    """将 NULL user_id 的记录分配给管理员"""

    # 需要迁移的表列表
    tables = [
        'news_sources',
        'news_articles',
        'scraper_runs',
        'export_tasks',
        'social_sessions',
        'proxy_configs',
        'account_credentials',
    ]

    for table in tables:
        op.execute(f"""
            UPDATE {table}
            SET user_id = '{ADMIN_USER_ID}'
            WHERE user_id IS NULL
        """)


def downgrade() -> None:
    """回滚：将管理员的记录设置回 NULL（仅用于测试）"""
    # 注意：此操作不可逆，因为无法区分原本就是管理员创建的数据
    # 和迁移过来的数据，因此 downgrade 不做任何操作
    pass
