"""Add user_id column to all business tables

Revision ID: 20251216_006
Revises: 20251216_005
Create Date: 2025-12-16

数据隔离基础设施：
- 为所有业务表添加 user_id 外键字段
- 为已有数据设置 user_id 为 admin (id=1)
- 添加索引优化查询性能
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251216_006'
down_revision: Union[str, None] = '20251216_005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为所有业务表添加 user_id 字段"""

    # ========== 1. news_sources 表 ==========
    op.add_column(
        'news_sources',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,  # 先允许 NULL，后续更新后再设置约束
            comment='所属用户ID'
        )
    )
    # 将已有数据归属到 admin (id=1)
    op.execute("UPDATE news_sources SET user_id = 1 WHERE user_id IS NULL")
    # 添加外键约束
    op.create_foreign_key(
        'fk_news_sources_user_id',
        'news_sources', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    # 设置 NOT NULL
    op.alter_column('news_sources', 'user_id', nullable=False)
    # 创建索引
    op.create_index('ix_news_sources_user_id', 'news_sources', ['user_id'])

    # ========== 2. news_articles 表 ==========
    op.add_column(
        'news_articles',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,
            comment='所属用户ID'
        )
    )
    op.execute("UPDATE news_articles SET user_id = 1 WHERE user_id IS NULL")
    op.create_foreign_key(
        'fk_news_articles_user_id',
        'news_articles', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.alter_column('news_articles', 'user_id', nullable=False)
    op.create_index('idx_article_user_date', 'news_articles', ['user_id', 'published_at'])

    # ========== 3. scraper_runs 表 ==========
    op.add_column(
        'scraper_runs',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,
            comment='所属用户ID'
        )
    )
    op.execute("UPDATE scraper_runs SET user_id = 1 WHERE user_id IS NULL")
    op.create_foreign_key(
        'fk_scraper_runs_user_id',
        'scraper_runs', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.alter_column('scraper_runs', 'user_id', nullable=False)
    op.create_index('ix_scraper_runs_user_id', 'scraper_runs', ['user_id'])

    # ========== 4. social_sessions 表 ==========
    op.add_column(
        'social_sessions',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,
            comment='所属用户ID'
        )
    )
    op.execute("UPDATE social_sessions SET user_id = 1 WHERE user_id IS NULL")
    op.create_foreign_key(
        'fk_social_sessions_user_id',
        'social_sessions', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.alter_column('social_sessions', 'user_id', nullable=False)
    op.create_index('idx_session_user_platform', 'social_sessions', ['user_id', 'platform'])

    # ========== 5. account_credentials 表 ==========
    op.add_column(
        'account_credentials',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,
            comment='所属用户ID'
        )
    )
    op.execute("UPDATE account_credentials SET user_id = 1 WHERE user_id IS NULL")
    op.create_foreign_key(
        'fk_account_credentials_user_id',
        'account_credentials', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.alter_column('account_credentials', 'user_id', nullable=False)
    op.create_index('ix_account_credentials_user_id', 'account_credentials', ['user_id'])

    # ========== 6. proxy_configs 表 ==========
    op.add_column(
        'proxy_configs',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,
            comment='所属用户ID'
        )
    )
    op.execute("UPDATE proxy_configs SET user_id = 1 WHERE user_id IS NULL")
    op.create_foreign_key(
        'fk_proxy_configs_user_id',
        'proxy_configs', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.alter_column('proxy_configs', 'user_id', nullable=False)
    op.create_index('ix_proxy_configs_user_id', 'proxy_configs', ['user_id'])

    # ========== 7. export_tasks 表 ==========
    op.add_column(
        'export_tasks',
        sa.Column(
            'user_id',
            sa.Integer(),
            nullable=True,
            comment='所属用户ID'
        )
    )
    op.execute("UPDATE export_tasks SET user_id = 1 WHERE user_id IS NULL")
    op.create_foreign_key(
        'fk_export_tasks_user_id',
        'export_tasks', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.alter_column('export_tasks', 'user_id', nullable=False)
    op.create_index('ix_export_tasks_user_id', 'export_tasks', ['user_id'])


def downgrade() -> None:
    """移除所有业务表的 user_id 字段"""

    # export_tasks
    op.drop_index('ix_export_tasks_user_id', table_name='export_tasks')
    op.drop_constraint('fk_export_tasks_user_id', 'export_tasks', type_='foreignkey')
    op.drop_column('export_tasks', 'user_id')

    # proxy_configs
    op.drop_index('ix_proxy_configs_user_id', table_name='proxy_configs')
    op.drop_constraint('fk_proxy_configs_user_id', 'proxy_configs', type_='foreignkey')
    op.drop_column('proxy_configs', 'user_id')

    # account_credentials
    op.drop_index('ix_account_credentials_user_id', table_name='account_credentials')
    op.drop_constraint('fk_account_credentials_user_id', 'account_credentials', type_='foreignkey')
    op.drop_column('account_credentials', 'user_id')

    # social_sessions
    op.drop_index('idx_session_user_platform', table_name='social_sessions')
    op.drop_constraint('fk_social_sessions_user_id', 'social_sessions', type_='foreignkey')
    op.drop_column('social_sessions', 'user_id')

    # scraper_runs
    op.drop_index('ix_scraper_runs_user_id', table_name='scraper_runs')
    op.drop_constraint('fk_scraper_runs_user_id', 'scraper_runs', type_='foreignkey')
    op.drop_column('scraper_runs', 'user_id')

    # news_articles
    op.drop_index('idx_article_user_date', table_name='news_articles')
    op.drop_constraint('fk_news_articles_user_id', 'news_articles', type_='foreignkey')
    op.drop_column('news_articles', 'user_id')

    # news_sources
    op.drop_index('ix_news_sources_user_id', table_name='news_sources')
    op.drop_constraint('fk_news_sources_user_id', 'news_sources', type_='foreignkey')
    op.drop_column('news_sources', 'user_id')
