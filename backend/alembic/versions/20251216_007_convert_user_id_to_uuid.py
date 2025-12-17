"""Convert user_id from Integer to UUID (CHAR(36))

Revision ID: 20251216_007
Revises: 20251216_006
Create Date: 2025-12-16

UUID 迁移：
- 将 users.id 从 INT 改为 CHAR(36)
- 将所有 user_id 外键从 INT 改为 CHAR(36)
- 创建系统用户 UUID
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext
import uuid

# revision identifiers, used by Alembic.
revision: str = '20251216_007'
down_revision: Union[str, None] = '20251216_006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 系统用户 UUID
SYSTEM_USER_UUID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    """将 user_id 从 Integer 转换为 UUID"""

    # 获取数据库连接
    connection = op.get_bind()

    # 1. 首先获取现有用户的映射关系（旧 INT id -> 新 UUID）
    # 查询现有用户
    result = connection.execute(sa.text("SELECT id, username FROM users"))
    users = list(result)

    # 创建 INT -> UUID 映射
    id_mapping = {}
    for user in users:
        old_id = user[0]
        username = user[1]
        if username == 'admin':
            # admin 用户使用系统用户 UUID
            new_uuid = SYSTEM_USER_UUID
        else:
            new_uuid = str(uuid.uuid4())
        id_mapping[old_id] = new_uuid

    # 2. 删除所有外键约束
    foreign_keys = [
        ('fk_news_sources_user_id', 'news_sources'),
        ('fk_news_articles_user_id', 'news_articles'),
        ('fk_scraper_runs_user_id', 'scraper_runs'),
        ('fk_social_sessions_user_id', 'social_sessions'),
        ('fk_account_credentials_user_id', 'account_credentials'),
        ('fk_proxy_configs_user_id', 'proxy_configs'),
        ('fk_export_tasks_user_id', 'export_tasks'),
    ]

    for fk_name, table in foreign_keys:
        try:
            op.drop_constraint(fk_name, table, type_='foreignkey')
        except Exception:
            pass  # 约束可能不存在

    # 3. 为所有业务表添加临时的 user_uuid 列
    tables_with_user_id = [
        'news_sources',
        'news_articles',
        'scraper_runs',
        'social_sessions',
        'account_credentials',
        'proxy_configs',
        'export_tasks',
    ]

    for table in tables_with_user_id:
        # 添加临时 UUID 列
        op.add_column(table, sa.Column('user_uuid_temp', sa.String(36), nullable=True))
        # 更新映射
        for old_id, new_uuid in id_mapping.items():
            connection.execute(
                sa.text(f"UPDATE {table} SET user_uuid_temp = :new_uuid WHERE user_id = :old_id"),
                {"new_uuid": new_uuid, "old_id": old_id}
            )

    # 4. 修改 users 表
    # 添加临时 UUID 列
    op.add_column('users', sa.Column('uuid_temp', sa.String(36), nullable=True))

    # 更新 UUID
    for old_id, new_uuid in id_mapping.items():
        connection.execute(
            sa.text("UPDATE users SET uuid_temp = :new_uuid WHERE id = :old_id"),
            {"new_uuid": new_uuid, "old_id": old_id}
        )

    # 删除旧的主键和 id 列
    op.drop_index('ix_users_id', table_name='users')
    op.drop_column('users', 'id')

    # 重命名 uuid_temp 为 id
    op.alter_column('users', 'uuid_temp', new_column_name='id', nullable=False)

    # 添加新的主键
    op.create_primary_key('pk_users', 'users', ['id'])
    op.create_index('ix_users_id', 'users', ['id'])

    # 5. 更新业务表的 user_id 列
    for table in tables_with_user_id:
        # 删除旧的 user_id 列
        try:
            index_name = f'ix_{table}_user_id'
            op.drop_index(index_name, table_name=table)
        except Exception:
            pass

        # 对于有复合索引的表，需要特别处理
        if table == 'news_articles':
            try:
                op.drop_index('idx_article_user_date', table_name=table)
            except Exception:
                pass
        elif table == 'social_sessions':
            try:
                op.drop_index('idx_session_user_platform', table_name=table)
            except Exception:
                pass

        op.drop_column(table, 'user_id')

        # 重命名临时列为 user_id
        op.alter_column(table, 'user_uuid_temp', new_column_name='user_id', nullable=False)

        # 重新创建索引
        op.create_index(f'ix_{table}_user_id', table, ['user_id'])

    # 重建复合索引
    op.create_index('idx_article_user_date', 'news_articles', ['user_id', 'published_at'])
    op.create_index('idx_session_user_platform', 'social_sessions', ['user_id', 'platform'])

    # 6. 重新添加外键约束
    for fk_name, table in foreign_keys:
        op.create_foreign_key(
            fk_name,
            table, 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """将 user_id 从 UUID 恢复为 Integer（不建议）"""
    # 由于 UUID 到 INT 的转换会丢失数据，这个 downgrade 只是示意
    # 实际使用中需要谨慎处理

    # 删除所有外键约束
    foreign_keys = [
        ('fk_news_sources_user_id', 'news_sources'),
        ('fk_news_articles_user_id', 'news_articles'),
        ('fk_scraper_runs_user_id', 'scraper_runs'),
        ('fk_social_sessions_user_id', 'social_sessions'),
        ('fk_account_credentials_user_id', 'account_credentials'),
        ('fk_proxy_configs_user_id', 'proxy_configs'),
        ('fk_export_tasks_user_id', 'export_tasks'),
    ]

    for fk_name, table in foreign_keys:
        try:
            op.drop_constraint(fk_name, table, type_='foreignkey')
        except Exception:
            pass

    # 为业务表恢复 INT user_id
    tables_with_user_id = [
        'news_sources',
        'news_articles',
        'scraper_runs',
        'social_sessions',
        'account_credentials',
        'proxy_configs',
        'export_tasks',
    ]

    for table in tables_with_user_id:
        try:
            op.drop_index(f'ix_{table}_user_id', table_name=table)
        except Exception:
            pass

        if table == 'news_articles':
            try:
                op.drop_index('idx_article_user_date', table_name=table)
            except Exception:
                pass
        elif table == 'social_sessions':
            try:
                op.drop_index('idx_session_user_platform', table_name=table)
            except Exception:
                pass

        op.drop_column(table, 'user_id')
        op.add_column(table, sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'))
        op.create_index(f'ix_{table}_user_id', table, ['user_id'])

    # 恢复复合索引
    op.create_index('idx_article_user_date', 'news_articles', ['user_id', 'published_at'])
    op.create_index('idx_session_user_platform', 'social_sessions', ['user_id', 'platform'])

    # 恢复 users 表的 INT id
    op.drop_index('ix_users_id', table_name='users')
    op.drop_constraint('pk_users', 'users', type_='primary')
    op.drop_column('users', 'id')
    op.add_column('users', sa.Column('id', sa.Integer(), autoincrement=True, nullable=False))
    op.create_primary_key('pk_users', 'users', ['id'])
    op.create_index('ix_users_id', 'users', ['id'])

    # 重新添加外键约束
    for fk_name, table in foreign_keys:
        op.create_foreign_key(
            fk_name,
            table, 'users',
            ['user_id'], ['id'],
            ondelete='CASCADE'
        )
