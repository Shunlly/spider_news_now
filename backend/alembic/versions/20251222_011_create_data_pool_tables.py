"""Create data pool tables

Revision ID: 011_data_pool
Revises: 010_add_missing_foreign_keys
Create Date: 2025-12-22

创建数据池相关表：
- data_pointers: 统一数据指针
- article_contents: 正文提取结果
- article_analyses: 分析结果
- user_data_relations: 用户数据关系
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR, JSON


# revision identifiers, used by Alembic.
revision = '20251222_011'
down_revision = '20251220_010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建 data_pointers 表
    op.create_table(
        'data_pointers',
        sa.Column('id', CHAR(36), primary_key=True),
        sa.Column('domain', sa.String(50), nullable=False, comment='数据域: news, twitter, telegram'),
        sa.Column('domain_table', sa.String(100), nullable=False, comment='域表名'),
        sa.Column('domain_id', sa.String(100), nullable=False, comment='域内记录ID'),
        sa.Column('visibility', sa.Enum('private', 'tenant_shared', 'public', name='datavisibility'),
                  nullable=False, server_default='private', comment='可见性'),
        sa.Column('created_by', CHAR(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tenant_id', sa.Integer, sa.ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('has_content', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('has_analysis', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('title', sa.String(500), nullable=True, comment='标题缓存'),
        sa.Column('url', sa.String(2000), nullable=True, comment='URL缓存'),
        sa.Column('platform', sa.String(50), nullable=True, comment='平台标识'),
        sa.Column('extra_metadata', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('domain', 'domain_table', 'domain_id', name='uq_data_pointer_ref'),
    )

    # 创建索引
    op.create_index('ix_data_pointer_domain', 'data_pointers', ['domain'])
    op.create_index('ix_data_pointer_visibility', 'data_pointers', ['visibility'])
    op.create_index('ix_data_pointer_created_by', 'data_pointers', ['created_by'])
    op.create_index('ix_data_pointer_tenant_id', 'data_pointers', ['tenant_id'])
    op.create_index('ix_data_pointer_created_at', 'data_pointers', ['created_at'])

    # 创建 article_contents 表
    op.create_table(
        'article_contents',
        sa.Column('id', CHAR(36), primary_key=True),
        sa.Column('pointer_id', CHAR(36), sa.ForeignKey('data_pointers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('content_text', sa.Text, nullable=True),
        sa.Column('content_html', sa.Text, nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=True),
        sa.Column('word_count', sa.Integer, nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_primary', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_index('ix_article_content_pointer', 'article_contents', ['pointer_id'])
    op.create_index('ix_article_content_primary', 'article_contents', ['pointer_id', 'is_primary'])

    # 创建 article_analyses 表
    op.create_table(
        'article_analyses',
        sa.Column('id', CHAR(36), primary_key=True),
        sa.Column('pointer_id', CHAR(36), sa.ForeignKey('data_pointers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),
        sa.Column('result', JSON, nullable=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_index('ix_article_analysis_pointer', 'article_analyses', ['pointer_id'])
    op.create_index('ix_article_analysis_type', 'article_analyses', ['pointer_id', 'analysis_type'])

    # 创建 user_data_relations 表
    op.create_table(
        'user_data_relations',
        sa.Column('id', CHAR(36), primary_key=True),
        sa.Column('user_id', CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pointer_id', CHAR(36), sa.ForeignKey('data_pointers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_favorited', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('is_bookmarked', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('user_tags', JSON, nullable=True),
        sa.Column('user_notes', sa.Text, nullable=True),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('read_at', sa.DateTime, nullable=True),
        sa.UniqueConstraint('user_id', 'pointer_id', name='uq_user_data_relation'),
    )

    op.create_index('ix_user_data_user', 'user_data_relations', ['user_id'])
    op.create_index('ix_user_data_pointer', 'user_data_relations', ['pointer_id'])
    op.create_index('ix_user_data_favorited', 'user_data_relations', ['user_id', 'is_favorited'])
    op.create_index('ix_user_data_bookmarked', 'user_data_relations', ['user_id', 'is_bookmarked'])


def downgrade() -> None:
    op.drop_table('user_data_relations')
    op.drop_table('article_analyses')
    op.drop_table('article_contents')
    op.drop_table('data_pointers')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS datavisibility")
