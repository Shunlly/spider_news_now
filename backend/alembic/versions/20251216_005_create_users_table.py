"""Create users table with default admin account

Revision ID: 20251216_005
Revises: 20251215_004
Create Date: 2025-12-16

用户认证基础设施：
- 用户表包含角色（admin/user）
- 登录尝试追踪和账户锁定
- 创建默认管理员账户（admin:admin123）
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision: str = '20251216_005'
down_revision: Union[str, None] = '20251215_004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 密码哈希上下文（与 app/core/security.py 保持一致）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def table_exists(table_name: str) -> bool:
    """检查表是否已存在"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :table_name"
    ), {"table_name": table_name})
    return result.scalar() > 0


def upgrade() -> None:
    """创建 users 表并插入默认管理员账户"""
    # 检查表是否已存在（防止重复创建）
    if table_exists('users'):
        return

    # MySQL 不需要单独创建 ENUM 类型，在列定义中直接使用
    # 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('username', sa.String(50), nullable=False, comment='用户名'),
        sa.Column('email', sa.String(100), nullable=True, comment='邮箱'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='密码哈希'),
        sa.Column(
            'role',
            sa.Enum('admin', 'user', name='user_role'),
            nullable=False,
            server_default='user',
            comment='用户角色：admin=管理员, user=普通用户'
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否激活'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='最后登录时间'),
        sa.Column('login_attempts', sa.Integer(), nullable=False, server_default='0', comment='登录尝试次数'),
        sa.Column('locked_until', sa.DateTime(), nullable=True, comment='账户锁定至'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # 生成默认管理员密码哈希
    admin_password_hash = pwd_context.hash('admin123')

    # 插入默认管理员账户
    op.execute(f"""
        INSERT INTO users (username, email, password_hash, role, is_active)
        VALUES ('admin', 'admin@example.com', '{admin_password_hash}', 'admin', TRUE)
    """)


def downgrade() -> None:
    """删除 users 表"""
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
    # MySQL 不需要单独删除 ENUM 类型，随表一起删除
