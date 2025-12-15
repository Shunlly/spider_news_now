"""add content_status and content_retry_count fields to news_articles

Revision ID: 20251215_004
Revises: 20251215_003
Create Date: 2025-12-15

支持两阶段抓取：
1. 第一阶段：快速抓取列表页，保存基础信息
2. 第二阶段：后台任务异步解析正文内容
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251215_004'
down_revision: Union[str, None] = '20251215_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add content_status and content_retry_count columns to news_articles table."""
    # 添加 content_status 字段
    op.add_column(
        'news_articles',
        sa.Column(
            'content_status',
            sa.String(20),
            nullable=False,
            server_default='pending',
            comment='正文解析状态：pending=待解析, parsing=解析中, completed=已完成, failed=失败'
        )
    )

    # 添加 content_retry_count 字段
    op.add_column(
        'news_articles',
        sa.Column(
            'content_retry_count',
            sa.Integer,
            nullable=False,
            server_default='0',
            comment='正文解析重试次数'
        )
    )

    # 创建索引以优化查询待解析文章的性能
    op.create_index(
        'idx_news_articles_content_status',
        'news_articles',
        ['content_status']
    )

    # 更新已有正文的文章状态为 completed
    op.execute("""
        UPDATE news_articles
        SET content_status = 'completed'
        WHERE content_url IS NOT NULL OR content_text IS NOT NULL
    """)


def downgrade() -> None:
    """Remove content_status and content_retry_count columns from news_articles table."""
    op.drop_index('idx_news_articles_content_status', table_name='news_articles')
    op.drop_column('news_articles', 'content_retry_count')
    op.drop_column('news_articles', 'content_status')
