"""Add missing foreign key constraints for business tables

Revision ID: 20251220_010
Revises: 20251220_009
Create Date: 2025-12-20

注意：此迁移已改为空操作
- 项目使用逻辑外键而非物理外键
- 保留此文件以维护迁移历史
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '20251220_010'
down_revision: Union[str, None] = '20251220_009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """使用逻辑外键，不添加物理外键约束"""
    pass


def downgrade() -> None:
    """使用逻辑外键，无需删除外键约束"""
    pass
