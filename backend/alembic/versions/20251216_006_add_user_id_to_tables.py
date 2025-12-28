"""Add user_id column to all business tables

Revision ID: 20251216_006
Revises: 20251216_005
Create Date: 2025-12-16

数据隔离基础设施：
- 为所有业务表添加 user_id 外键字段
- 为已有数据设置 user_id 为 admin (id=1)
- 添加索引优化查询性能
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251216_006'
down_revision: str | None = '20251216_005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """检查索引是否已存在"""
    bind = op.get_bind()
    insp = inspect(bind)
    indexes = [idx['name'] for idx in insp.get_indexes(table_name)]
    return index_name in indexes


def fk_exists(table_name: str, fk_name: str) -> bool:
    """检查外键是否已存在"""
    bind = op.get_bind()
    insp = inspect(bind)
    fks = [fk['name'] for fk in insp.get_foreign_keys(table_name)]
    return fk_name in fks


def add_user_id_column(table_name: str, fk_name: str, index_name: str) -> None:
    """为表添加 user_id 列、外键和索引（幂等操作）"""
    # 添加列（如果不存在）
    if not column_exists(table_name, 'user_id'):
        op.add_column(
            table_name,
            sa.Column(
                'user_id',
                sa.Integer(),
                nullable=True,
                comment='所属用户ID'
            )
        )
        # 将已有数据归属到 admin (id=1)
        op.execute(f"UPDATE {table_name} SET user_id = 1 WHERE user_id IS NULL")
        # 设置 NOT NULL
        op.alter_column(table_name, 'user_id', nullable=False)

    # 添加外键（如果不存在）
    if not fk_exists(table_name, fk_name):
        op.create_foreign_key(
            fk_name,
            table_name, 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )

    # 添加索引（如果不存在）
    if not index_exists(table_name, index_name):
        op.create_index(index_name, table_name, ['user_id'])


def upgrade() -> None:
    """为所有业务表添加 user_id 字段"""

    # ========== 1. news_sources 表 ==========
    add_user_id_column('news_sources', 'fk_news_sources_user_id', 'ix_news_sources_user_id')

    # ========== 2. news_articles 表 ==========
    if not column_exists('news_articles', 'user_id'):
        op.add_column(
            'news_articles',
            sa.Column('user_id', sa.Integer(), nullable=True, comment='所属用户ID')
        )
        op.execute("UPDATE news_articles SET user_id = 1 WHERE user_id IS NULL")
        op.alter_column('news_articles', 'user_id', nullable=False)
    if not fk_exists('news_articles', 'fk_news_articles_user_id'):
        op.create_foreign_key(
            'fk_news_articles_user_id',
            'news_articles', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
    if not index_exists('news_articles', 'idx_article_user_date'):
        op.create_index('idx_article_user_date', 'news_articles', ['user_id', 'published_at'])

    # ========== 3. scraper_runs 表 ==========
    add_user_id_column('scraper_runs', 'fk_scraper_runs_user_id', 'ix_scraper_runs_user_id')

    # ========== 4. social_sessions 表 ==========
    if not column_exists('social_sessions', 'user_id'):
        op.add_column(
            'social_sessions',
            sa.Column('user_id', sa.Integer(), nullable=True, comment='所属用户ID')
        )
        op.execute("UPDATE social_sessions SET user_id = 1 WHERE user_id IS NULL")
        op.alter_column('social_sessions', 'user_id', nullable=False)
    if not fk_exists('social_sessions', 'fk_social_sessions_user_id'):
        op.create_foreign_key(
            'fk_social_sessions_user_id',
            'social_sessions', 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
    if not index_exists('social_sessions', 'idx_session_user_platform'):
        op.create_index('idx_session_user_platform', 'social_sessions', ['user_id', 'platform'])

    # ========== 5. account_credentials 表 ==========
    add_user_id_column('account_credentials', 'fk_account_credentials_user_id', 'ix_account_credentials_user_id')

    # ========== 6. proxy_configs 表 ==========
    add_user_id_column('proxy_configs', 'fk_proxy_configs_user_id', 'ix_proxy_configs_user_id')

    # ========== 7. export_tasks 表 ==========
    add_user_id_column('export_tasks', 'fk_export_tasks_user_id', 'ix_export_tasks_user_id')


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
