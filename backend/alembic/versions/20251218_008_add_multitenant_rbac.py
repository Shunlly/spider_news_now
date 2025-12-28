"""Add multi-tenant and RBAC tables

Revision ID: 20251218_008
Revises: 20251216_007
Create Date: 2025-12-18

多租户 SaaS 迁移：
- tenants: 租户表
- roles: 角色表（RBAC）
- quotas: 配额追踪表
- audit_logs: 审计日志表
- captcha_attempts: 验证码尝试表
- 更新 users 表添加 tenant_id, role_id 等字段
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20251218_008'
down_revision: Union[str, None] = '20251216_007'
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


def column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = :table_name AND column_name = :column_name"
    ), {"table_name": table_name, "column_name": column_name})
    return result.scalar() > 0


def foreign_key_exists(constraint_name: str) -> bool:
    """检查外键约束是否已存在"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.table_constraints "
        "WHERE table_schema = DATABASE() AND constraint_name = :constraint_name AND constraint_type = 'FOREIGN KEY'"
    ), {"constraint_name": constraint_name})
    return result.scalar() > 0


def index_exists(index_name: str, table_name: str) -> bool:
    """检查索引是否已存在"""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.statistics "
        "WHERE table_schema = DATABASE() AND table_name = :table_name AND index_name = :index_name"
    ), {"table_name": table_name, "index_name": index_name})
    return result.scalar() > 0


def upgrade() -> None:
    """添加多租户和 RBAC 相关表"""

    # 1. 创建 tenants 表（租户）
    if not table_exists('tenants'):
        op.create_table(
            'tenants',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='租户ID'),
            sa.Column('name', sa.String(100), nullable=False, comment='租户名称'),
            sa.Column('display_name', sa.String(200), nullable=True, comment='显示名称'),
            sa.Column('description', sa.Text(), nullable=True, comment='描述'),
            sa.Column('quota_config', sa.JSON(), nullable=False, comment='配额配置'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否激活'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name', name='uq_tenants_name'),
        )
        op.create_index('ix_tenants_id', 'tenants', ['id'])
        op.create_index('ix_tenants_name', 'tenants', ['name'])

    # 2. 创建 roles 表（角色）
    if not table_exists('roles'):
        op.create_table(
            'roles',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='角色ID'),
            sa.Column('name', sa.String(50), nullable=False, comment='角色标识'),
            sa.Column('display_name', sa.String(100), nullable=True, comment='显示名称'),
            sa.Column('description', sa.Text(), nullable=True, comment='描述'),
            sa.Column('permissions', sa.JSON(), nullable=False, comment='权限列表'),
            sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0', comment='是否为系统角色'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name', name='uq_roles_name'),
        )
        op.create_index('ix_roles_id', 'roles', ['id'])
        op.create_index('ix_roles_name', 'roles', ['name'])

        # 3. 插入预定义角色（仅当 roles 表是新创建时）
        op.execute("""
            INSERT INTO roles (id, name, display_name, description, permissions, is_system) VALUES
            (1, 'super_admin', '超级管理员', '系统最高权限，可管理所有租户', '["*"]', 1),
            (2, 'tenant_admin', '租户管理员', '租户内最高权限，可管理本租户用户和数据', '["user:read","user:create","user:update","user:delete","task:read","task:create","task:update","task:delete","task:run","task:cancel","news:read","news:create","news:delete","news:export","social:read","social:create","social:delete","social:export","proxy:read","proxy:create","proxy:update","proxy:delete","credential:read","credential:create","credential:update","credential:delete","export:read","export:create","audit:read","tenant:read","tenant:update"]', 1),
            (3, 'user', '普通用户', '普通用户权限，只能管理自己的数据', '["user:read","task:read","task:create","task:run","task:cancel","news:read","news:export","social:read","social:export","proxy:read","credential:read","export:read","export:create"]', 1)
        """)

    # 4. 添加 users 表新字段
    if not column_exists('users', 'tenant_id'):
        op.add_column('users', sa.Column('tenant_id', sa.Integer(), nullable=True, comment='所属租户ID（超级管理员可为空）'))
    if not column_exists('users', 'role_id'):
        op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=False, server_default='3', comment='角色ID'))
    if not column_exists('users', 'quota_tier'):
        op.add_column('users', sa.Column('quota_tier', sa.String(20), nullable=False, server_default='free', comment='配额等级'))
    if not column_exists('users', 'is_verified'):
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0', comment='邮箱是否已验证'))
    if not column_exists('users', 'verification_token'):
        op.add_column('users', sa.Column('verification_token', sa.String(100), nullable=True, comment='邮箱验证Token'))
    if not column_exists('users', 'verification_expires'):
        op.add_column('users', sa.Column('verification_expires', sa.DateTime(), nullable=True, comment='验证Token过期时间'))
    # 注意：last_login_at, login_attempts, locked_until 已在 005 迁移中创建，此处不再重复添加

    # 创建索引（不使用物理外键，使用逻辑外键）
    if not index_exists('ix_users_tenant_id', 'users'):
        op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    if not index_exists('ix_users_role_id', 'users'):
        op.create_index('ix_users_role_id', 'users', ['role_id'])

    # 5. 创建 quotas 表（配额追踪）- 使用逻辑外键
    if not table_exists('quotas'):
        op.create_table(
            'quotas',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='配额ID'),
            sa.Column('user_id', sa.String(36), nullable=False, comment='用户ID'),
            sa.Column('tier', sa.String(20), nullable=False, server_default='free', comment='配额等级'),
            sa.Column('daily_limit', sa.Integer(), nullable=False, server_default='100', comment='每日采集限额'),
            sa.Column('daily_used', sa.Integer(), nullable=False, server_default='0', comment='今日已使用量'),
            sa.Column('concurrent_limit', sa.Integer(), nullable=False, server_default='1', comment='并发任务限额'),
            sa.Column('concurrent_used', sa.Integer(), nullable=False, server_default='0', comment='当前并发使用数'),
            sa.Column('reset_at', sa.DateTime(), nullable=False, comment='配额重置时间'),
            sa.Column('warning_shown', sa.Boolean(), nullable=False, server_default='0', comment='是否已显示配额警告'),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', name='uq_quotas_user_id'),
        )
        op.create_index('ix_quotas_user_id', 'quotas', ['user_id'])

    # 6. 创建 audit_logs 表（审计日志）- 使用逻辑外键
    if not table_exists('audit_logs'):
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='日志ID'),
            sa.Column('user_id', sa.String(36), nullable=True, comment='操作用户ID'),
            sa.Column('user_email', sa.String(255), nullable=True, comment='用户邮箱（快照）'),
            sa.Column('action', sa.String(50), nullable=False, comment='操作类型'),
            sa.Column('resource_type', sa.String(50), nullable=False, comment='资源类型'),
            sa.Column('resource_id', sa.String(100), nullable=True, comment='资源ID'),
            sa.Column('ip_address', sa.String(45), nullable=False, comment='来源IP地址'),
            sa.Column('user_agent', sa.String(500), nullable=True, comment='用户代理字符串'),
            sa.Column('details', sa.JSON(), nullable=False, comment='操作详情'),
            sa.Column('description', sa.Text(), nullable=True, comment='操作描述'),
            sa.Column('success', sa.Boolean(), nullable=False, server_default='1', comment='操作是否成功'),
            sa.Column('error_message', sa.Text(), nullable=True, comment='错误消息'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='操作时间'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
        op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
        op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
        op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])

    # 7. 创建 captcha_attempts 表（验证码尝试）
    if not table_exists('captcha_attempts'):
        op.create_table(
            'captcha_attempts',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='记录ID'),
            sa.Column('identifier', sa.String(100), nullable=False, comment='标识符（IP或邮箱）'),
            sa.Column('captcha_id', sa.String(100), nullable=True, comment='验证码会话ID'),
            sa.Column('success', sa.Boolean(), nullable=False, server_default='0', comment='验证是否成功'),
            sa.Column('ip_address', sa.String(45), nullable=False, comment='来源IP地址'),
            sa.Column('user_agent', sa.String(500), nullable=True, comment='用户代理字符串'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='尝试时间'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_captcha_attempts_identifier', 'captcha_attempts', ['identifier'])
        op.create_index('ix_captcha_attempts_created_at', 'captcha_attempts', ['created_at'])

    # 8. 更新现有 admin 用户为超级管理员角色
    # 只使用 username 查询，避免 id 列可能不存在的问题
    op.execute("""
        UPDATE users
        SET role_id = 1, is_verified = 1
        WHERE username = 'admin'
    """)


def downgrade() -> None:
    """回滚多租户相关表"""

    # 删除 captcha_attempts 表
    op.drop_index('ix_captcha_attempts_created_at', table_name='captcha_attempts')
    op.drop_index('ix_captcha_attempts_identifier', table_name='captcha_attempts')
    op.drop_table('captcha_attempts')

    # 删除 audit_logs 表
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')

    # 删除 quotas 表
    op.drop_index('ix_quotas_user_id', table_name='quotas')
    op.drop_table('quotas')

    # 删除 users 表新增字段
    op.drop_index('ix_users_role_id', table_name='users')
    op.drop_index('ix_users_tenant_id', table_name='users')
    # 注意：不删除外键约束，因为使用逻辑外键
    # 注意：last_login_at, login_attempts, locked_until 由 005 迁移创建，此处不删除
    op.drop_column('users', 'verification_expires')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'quota_tier')
    op.drop_column('users', 'role_id')
    op.drop_column('users', 'tenant_id')

    # 删除 roles 表
    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_index('ix_roles_id', table_name='roles')
    op.drop_table('roles')

    # 删除 tenants 表
    op.drop_index('ix_tenants_name', table_name='tenants')
    op.drop_index('ix_tenants_id', table_name='tenants')
    op.drop_table('tenants')
