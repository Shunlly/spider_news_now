"""add content_url field to news_articles

Revision ID: 20251215_003
Revises: 20251214_002
Create Date: 2025-12-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251215_003'
down_revision: Union[str, None] = '002_social_and_infra'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add content_url column to news_articles table."""
    op.add_column(
        'news_articles',
        sa.Column(
            'content_url',
            sa.String(512),
            nullable=True,
            comment='正文存储路径（MinIO/RustFS）'
        )
    )


def downgrade() -> None:
    """Remove content_url column from news_articles table."""
    op.drop_column('news_articles', 'content_url')
