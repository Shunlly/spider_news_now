"""Convert user_id from Integer to UUID (CHAR(36))

Revision ID: 20251216_007
Revises: 20251216_006
Create Date: 2025-12-16

UUID 迁移：
- 将 users.id 从 INT 改为 CHAR(36)
- 将所有 user_id 外键从 INT 改为 CHAR(36)
- 创建系统用户 UUID
"""
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from passlib.context import CryptContext
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20251216_007'
down_revision: str | None = '20251216_006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 系统用户 UUID
SYSTEM_USER_UUID = "00000000-0000-0000-0000-000000000001"


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


def table_exists(table_name: str) -> bool:
    """检查表是否已存在"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :table_name"
    ), {"table_name": table_name})
    return result.scalar() > 0


def get_column_type(table_name: str, column_name: str) -> str:
    """获取列的类型"""
    bind = op.get_bind()
    insp = inspect(bind)
    for col in insp.get_columns(table_name):
        if col['name'] == column_name:
            return str(col['type'])
    return ''


def upgrade() -> None:
    """将 user_id 从 Integer 转换为 UUID"""

    # 获取数据库连接
    connection = op.get_bind()

    # 检查 users 表是否存在
    if not table_exists('users'):
        # users 表不存在，跳过此迁移
        return

    # 检查 users 表是否有 id 列
    if not column_exists('users', 'id'):
        # id 列不存在，跳过此迁移
        return

    # 检查 users.id 是否已经是 UUID 类型（CHAR(36) 或 VARCHAR(36)）
    id_type = get_column_type('users', 'id')
    if not id_type:
        # 无法获取列类型，跳过
        return
    if 'CHAR' in id_type.upper() or 'VARCHAR' in id_type.upper():
        # 已经是 UUID 类型，跳过迁移
        return

    # 1. 首先获取现有用户的映射关系（旧 INT id -> 新 UUID）
    # 查询现有用户
    try:
        result = connection.execute(sa.text("SELECT id, username FROM users"))
        users = list(result)
    except Exception:
        # 查询失败，可能表结构不正确，跳过
        users = []

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
        if table_exists(table) and fk_exists(table, fk_name):
            op.drop_constraint(fk_name, table, type_='foreignkey')

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
        # 跳过不存在的表
        if not table_exists(table):
            continue
        # 添加临时 UUID 列（如果不存在）
        if not column_exists(table, 'user_uuid_temp'):
            op.add_column(table, sa.Column('user_uuid_temp', sa.String(36), nullable=True))
            # 更新映射
            for old_id, new_uuid in id_mapping.items():
                connection.execute(
                    sa.text(f"UPDATE {table} SET user_uuid_temp = :new_uuid WHERE user_id = :old_id"),
                    {"new_uuid": new_uuid, "old_id": old_id}
                )

    # 4. 修改 users 表
    # 添加临时 UUID 列（如果不存在）
    if not column_exists('users', 'uuid_temp'):
        op.add_column('users', sa.Column('uuid_temp', sa.String(36), nullable=True))

        # 更新 UUID
        for old_id, new_uuid in id_mapping.items():
            connection.execute(
                sa.text("UPDATE users SET uuid_temp = :new_uuid WHERE id = :old_id"),
                {"new_uuid": new_uuid, "old_id": old_id}
            )

    # 删除旧的主键和 id 列
    if index_exists('users', 'ix_users_id'):
        op.drop_index('ix_users_id', table_name='users')
    if column_exists('users', 'id') and get_column_type('users', 'id').upper().startswith('INT'):
        op.drop_column('users', 'id')

    # 重命名 uuid_temp 为 id（如果存在）
    if column_exists('users', 'uuid_temp'):
        op.alter_column('users', 'uuid_temp', new_column_name='id', nullable=False)

    # 添加新的主键
    op.create_primary_key('pk_users', 'users', ['id'])
    if not index_exists('users', 'ix_users_id'):
        op.create_index('ix_users_id', 'users', ['id'])

    # 5. 更新业务表的 user_id 列
    for table in tables_with_user_id:
        # 跳过不存在的表
        if not table_exists(table):
            continue

        # 删除旧的 user_id 列（如果是 INT 类型）
        user_id_type = get_column_type(table, 'user_id')
        if user_id_type and 'INT' in user_id_type.upper():
            index_name = f'ix_{table}_user_id'
            if index_exists(table, index_name):
                op.drop_index(index_name, table_name=table)

            # 对于有复合索引的表，需要特别处理
            if table == 'news_articles' and index_exists(table, 'idx_article_user_date'):
                op.drop_index('idx_article_user_date', table_name=table)
            elif table == 'social_sessions' and index_exists(table, 'idx_session_user_platform'):
                op.drop_index('idx_session_user_platform', table_name=table)

            op.drop_column(table, 'user_id')

        # 重命名临时列为 user_id（如果存在）
        if column_exists(table, 'user_uuid_temp'):
            op.alter_column(table, 'user_uuid_temp', new_column_name='user_id', nullable=False)

        # 重新创建索引（如果不存在）
        if not index_exists(table, f'ix_{table}_user_id'):
            op.create_index(f'ix_{table}_user_id', table, ['user_id'])

    # 重建复合索引
    if table_exists('news_articles') and not index_exists('news_articles', 'idx_article_user_date'):
        op.create_index('idx_article_user_date', 'news_articles', ['user_id', 'published_at'])
    if table_exists('social_sessions') and not index_exists('social_sessions', 'idx_session_user_platform'):
        op.create_index('idx_session_user_platform', 'social_sessions', ['user_id', 'platform'])

    # 6. 重新添加外键约束
    for fk_name, table in foreign_keys:
        if table_exists(table) and not fk_exists(table, fk_name):
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
