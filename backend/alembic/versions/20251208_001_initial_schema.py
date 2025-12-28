"""Initial schema with news_sources, news_articles, scraper_runs tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-12-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """检查表是否已存在"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :table_name"
    ), {"table_name": table_name})
    return result.scalar() > 0


def upgrade() -> None:
    # Create news_sources table
    if not table_exists('news_sources'):
        op.create_table(
            'news_sources',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_key', sa.String(length=50), nullable=False),
            sa.Column('display_name', sa.String(length=100), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('scraper_module', sa.String(length=100), nullable=False),
            sa.Column('schedule_interval', sa.Integer(), nullable=False, server_default='1800'),
            sa.Column('last_run_at', sa.DateTime(), nullable=True),
            sa.Column('last_success_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='idle'),
            sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_news_sources_id', 'news_sources', ['id'])
        op.create_index('ix_news_sources_source_key', 'news_sources', ['source_key'], unique=True)

        # Seed initial news sources (6 sources)
        op.execute("""
            INSERT INTO news_sources (source_key, display_name, scraper_module, enabled)
            VALUES
                ('sina', '新浪新闻', 'app.scrapers.sina_scraper', TRUE),
                ('qq', '腾讯新闻', 'app.scrapers.qq_scraper', TRUE),
                ('wangyi', '网易新闻', 'app.scrapers.wangyi_scraper', TRUE),
                ('yicai', '第一财经', 'app.scrapers.yicai_scraper', TRUE),
                ('huanqiu', '环球网', 'app.scrapers.huanqiu_scraper', TRUE),
                ('ifeng', '凤凰网', 'app.scrapers.ifeng_scraper', TRUE)
        """)

    # Create news_articles table
    if not table_exists('news_articles'):
        op.create_table(
            'news_articles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('url_hash', sa.String(length=64), nullable=False),
            sa.Column('url', sa.String(length=512), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content_hash', sa.String(length=64), nullable=True),
            sa.Column('source_key', sa.String(length=50), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=False),
            sa.Column('scraped_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            # 使用逻辑外键，不添加物理外键约束
        )
        op.create_index('ix_news_articles_id', 'news_articles', ['id'])
        op.create_index('ix_news_articles_url_hash', 'news_articles', ['url_hash'], unique=True)
        op.create_index('ix_news_articles_title', 'news_articles', ['title'])
        op.create_index('ix_news_articles_content_hash', 'news_articles', ['content_hash'])
        op.create_index('ix_news_articles_source_key', 'news_articles', ['source_key'])
        op.create_index('ix_news_articles_category', 'news_articles', ['category'])
        op.create_index('idx_source_category_date', 'news_articles',
                        ['source_key', 'category', 'published_at'])

    # Create scraper_runs table
    if not table_exists('scraper_runs'):
        op.create_table(
            'scraper_runs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_key', sa.String(length=50), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('articles_scraped', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('articles_new', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('articles_duplicate', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('duration_seconds', sa.Integer(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('error_traceback', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            # 使用逻辑外键，不添加物理外键约束
        )
        op.create_index('ix_scraper_runs_id', 'scraper_runs', ['id'])
        op.create_index('ix_scraper_runs_source_key', 'scraper_runs', ['source_key'])
        op.create_index('idx_source_started', 'scraper_runs', ['source_key', 'started_at'])
        op.create_index('idx_status_started', 'scraper_runs', ['status', 'started_at'])


def downgrade() -> None:
    op.drop_table('scraper_runs')
    op.drop_table('news_articles')
    op.drop_table('news_sources')
