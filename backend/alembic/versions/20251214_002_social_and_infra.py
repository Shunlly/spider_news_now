"""Add social data, credentials, proxy, storage, and export tables

Revision ID: 002_social_and_infra
Revises: 001_initial_schema
Create Date: 2025-12-14

新增表：
- social_sessions: 社交数据会话表
- social_messages: 社交消息表
- account_credentials: 账号凭证表
- proxy_configs: 代理配置表
- storage_files: 存储文件元数据表
- export_tasks: 数据导出任务表

修改表：
- news_articles: 添加 content_text 和 simhash 字段用于全文搜索和去重
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_social_and_infra'
down_revision: Union[str, None] = '001_initial_schema'
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


def upgrade() -> None:
    # =============================================================
    # 1. 修改 news_articles 表，添加全文搜索和去重字段
    # =============================================================
    if not column_exists('news_articles', 'content_text'):
        op.add_column('news_articles',
            sa.Column('content_text', sa.Text(), nullable=True,
                      comment='正文纯文本（用于全文搜索）')
        )
    if not column_exists('news_articles', 'simhash'):
        op.add_column('news_articles',
            sa.Column('simhash', sa.BigInteger(), nullable=True,
                      comment='内容 SimHash 指纹')
        )
        op.create_index('ix_news_articles_simhash', 'news_articles', ['simhash'])

    # =============================================================
    # 2. 创建 social_sessions 表
    # =============================================================
    if not table_exists('social_sessions'):
        op.create_table(
            'social_sessions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_key', sa.String(length=100), nullable=False,
                      comment='会话唯一标识'),
            sa.Column('platform', sa.Enum('twitter', 'telegram', name='platform'),
                      nullable=False, comment='社交平台类型'),
            sa.Column('target_id', sa.String(length=100), nullable=False,
                      comment='目标账号 ID'),
            sa.Column('target_name', sa.String(length=100), nullable=False,
                      comment='目标显示名称'),
            sa.Column('target_username', sa.String(length=100), nullable=True,
                      comment='目标用户名'),
            sa.Column('target_type', sa.Enum('user', 'channel', 'group', 'hashtag',
                                              name='targettype'),
                      nullable=False, server_default='user', comment='目标类型'),
            sa.Column('description', sa.Text(), nullable=True,
                      comment='会话描述'),
            sa.Column('status', sa.Enum('active', 'paused', 'completed', 'error',
                                         name='sessionstatus'),
                      nullable=False, server_default='active', comment='会话状态'),
            sa.Column('message_count', sa.Integer(), nullable=False, server_default='0',
                      comment='消息总数'),
            sa.Column('last_message_at', sa.DateTime(), nullable=True,
                      comment='最后消息时间'),
            sa.Column('fetch_interval', sa.Integer(), nullable=False, server_default='3600',
                      comment='采集间隔（秒）'),
            sa.Column('last_fetch_at', sa.DateTime(), nullable=True,
                      comment='最后采集时间'),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            comment='社交数据会话表'
        )
        op.create_index('ix_social_sessions_id', 'social_sessions', ['id'])
        op.create_index('ix_social_sessions_session_key', 'social_sessions',
                        ['session_key'], unique=True)
        op.create_index('ix_social_sessions_platform', 'social_sessions', ['platform'])
        op.create_index('ix_social_sessions_target_id', 'social_sessions', ['target_id'])
        op.create_index('ix_social_sessions_status', 'social_sessions', ['status'])
        op.create_index('idx_platform_status', 'social_sessions', ['platform', 'status'])
        op.create_index('idx_platform_target', 'social_sessions', ['platform', 'target_id'])

    # =============================================================
    # 3. 创建 social_messages 表
    # =============================================================
    if not table_exists('social_messages'):
        op.create_table(
            'social_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.Integer(), nullable=False,
                      comment='所属会话 ID'),
            sa.Column('message_id', sa.String(length=100), nullable=False,
                      comment='平台消息 ID'),
            sa.Column('message_hash', sa.String(length=64), nullable=False,
                      comment='消息哈希（去重）'),
            sa.Column('author_id', sa.String(length=100), nullable=False,
                      comment='发送者 ID'),
            sa.Column('author_name', sa.String(length=100), nullable=False,
                      comment='发送者显示名'),
            sa.Column('author_username', sa.String(length=100), nullable=True,
                      comment='发送者用户名'),
            sa.Column('content', sa.Text(), nullable=True,
                      comment='消息文本内容'),
            sa.Column('content_html', sa.Text(), nullable=True,
                      comment='消息 HTML 格式'),
            sa.Column('simhash', sa.BigInteger(), nullable=True,
                      comment='内容 SimHash 指纹'),
            sa.Column('media_urls', sa.Text(), nullable=True,
                      comment='媒体 URL 列表（JSON）'),
            sa.Column('media_local_paths', sa.Text(), nullable=True,
                      comment='本地存储路径（JSON）'),
            sa.Column('reply_count', sa.Integer(), nullable=False, server_default='0',
                      comment='回复数'),
            sa.Column('repost_count', sa.Integer(), nullable=False, server_default='0',
                      comment='转发数'),
            sa.Column('like_count', sa.Integer(), nullable=False, server_default='0',
                      comment='点赞数'),
            sa.Column('view_count', sa.Integer(), nullable=False, server_default='0',
                      comment='浏览数'),
            sa.Column('reply_to_id', sa.String(length=100), nullable=True,
                      comment='回复的消息 ID'),
            sa.Column('repost_of_id', sa.String(length=100), nullable=True,
                      comment='转发的原消息 ID'),
            sa.Column('raw_data', sa.Text(), nullable=True,
                      comment='原始 JSON 数据'),
            sa.Column('posted_at', sa.DateTime(), nullable=False,
                      comment='消息发布时间'),
            sa.Column('fetched_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now(), comment='消息采集时间'),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            # 使用逻辑外键，不添加物理外键约束
            comment='社交消息表'
        )
        op.create_index('ix_social_messages_id', 'social_messages', ['id'])
        op.create_index('ix_social_messages_session_id', 'social_messages', ['session_id'])
        op.create_index('ix_social_messages_message_id', 'social_messages', ['message_id'])
        op.create_index('ix_social_messages_message_hash', 'social_messages',
                        ['message_hash'], unique=True)
        op.create_index('ix_social_messages_author_id', 'social_messages', ['author_id'])
        op.create_index('ix_social_messages_simhash', 'social_messages', ['simhash'])
        op.create_index('ix_social_messages_posted_at', 'social_messages', ['posted_at'])
        op.create_index('idx_session_posted', 'social_messages', ['session_id', 'posted_at'])
        op.create_index('idx_author_posted', 'social_messages', ['author_id', 'posted_at'])
        op.create_index('idx_session_message', 'social_messages',
                        ['session_id', 'message_id'], unique=True)

    # =============================================================
    # 4. 创建 account_credentials 表
    # =============================================================
    if not table_exists('account_credentials'):
        op.create_table(
            'account_credentials',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False,
                      comment='凭证名称'),
            sa.Column('platform', sa.Enum('twitter', 'telegram', name='platform'),
                      nullable=False, comment='社交平台类型'),
            sa.Column('status', sa.Enum('active', 'rate_limited', 'expired',
                                         'disabled', 'error', name='credentialstatus'),
                      nullable=False, server_default='active', comment='凭证状态'),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0',
                      comment='是否为默认凭证'),
            sa.Column('credentials_encrypted', sa.Text(), nullable=False,
                      comment='加密的凭证 JSON'),
            sa.Column('request_count', sa.Integer(), nullable=False, server_default='0',
                      comment='请求次数'),
            sa.Column('error_count', sa.Integer(), nullable=False, server_default='0',
                      comment='错误次数'),
            sa.Column('last_used_at', sa.DateTime(), nullable=True,
                      comment='最后使用时间'),
            sa.Column('last_error_at', sa.DateTime(), nullable=True,
                      comment='最后错误时间'),
            sa.Column('last_error_message', sa.Text(), nullable=True,
                      comment='最后错误信息'),
            sa.Column('rate_limit_reset_at', sa.DateTime(), nullable=True,
                      comment='限流重置时间'),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            comment='社交平台账号凭证表'
        )
        op.create_index('ix_account_credentials_id', 'account_credentials', ['id'])
        op.create_index('ix_account_credentials_name', 'account_credentials', ['name'])
        op.create_index('ix_account_credentials_platform', 'account_credentials', ['platform'])
        op.create_index('ix_account_credentials_status', 'account_credentials', ['status'])
        op.create_index('idx_cred_platform_status', 'account_credentials',
                        ['platform', 'status'])
        op.create_index('idx_cred_platform_default', 'account_credentials',
                        ['platform', 'is_default'])

    # =============================================================
    # 5. 创建 proxy_configs 表
    # =============================================================
    if not table_exists('proxy_configs'):
        op.create_table(
            'proxy_configs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False,
                      comment='代理名称'),
            sa.Column('protocol', sa.Enum('http', 'https', 'socks4', 'socks5',
                                           name='proxyprotocol'),
                      nullable=False, server_default='http', comment='代理协议'),
            sa.Column('host', sa.String(length=255), nullable=False,
                      comment='代理主机'),
            sa.Column('port', sa.Integer(), nullable=False,
                      comment='代理端口'),
            sa.Column('username', sa.String(length=100), nullable=True,
                      comment='认证用户名'),
            sa.Column('password_encrypted', sa.String(length=255), nullable=True,
                      comment='加密的密码'),
            sa.Column('status', sa.Enum('active', 'testing', 'failed', 'disabled',
                                         name='proxystatus'),
                      nullable=False, server_default='active', comment='代理状态'),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1',
                      comment='是否启用'),
            sa.Column('weight', sa.Integer(), nullable=False, server_default='1',
                      comment='权重'),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='0',
                      comment='优先级'),
            sa.Column('request_count', sa.Integer(), nullable=False, server_default='0',
                      comment='请求次数'),
            sa.Column('success_count', sa.Integer(), nullable=False, server_default='0',
                      comment='成功次数'),
            sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0',
                      comment='失败次数'),
            sa.Column('avg_response_time', sa.Float(), nullable=True,
                      comment='平均响应时间（ms）'),
            sa.Column('last_response_time', sa.Float(), nullable=True,
                      comment='最后响应时间（ms）'),
            sa.Column('last_check_at', sa.DateTime(), nullable=True,
                      comment='最后检查时间'),
            sa.Column('last_success_at', sa.DateTime(), nullable=True,
                      comment='最后成功时间'),
            sa.Column('last_failure_at', sa.DateTime(), nullable=True,
                      comment='最后失败时间'),
            sa.Column('last_error_message', sa.Text(), nullable=True,
                      comment='最后错误信息'),
            sa.Column('notes', sa.Text(), nullable=True,
                      comment='备注'),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            comment='代理配置表'
        )
        op.create_index('ix_proxy_configs_id', 'proxy_configs', ['id'])
        op.create_index('ix_proxy_configs_name', 'proxy_configs', ['name'])
        op.create_index('ix_proxy_configs_status', 'proxy_configs', ['status'])
        op.create_index('idx_proxy_status_enabled', 'proxy_configs', ['status', 'enabled'])
        op.create_index('idx_proxy_priority_weight', 'proxy_configs', ['priority', 'weight'])

    # =============================================================
    # 6. 创建 storage_files 表
    # =============================================================
    if not table_exists('storage_files'):
        op.create_table(
            'storage_files',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('file_key', sa.String(length=255), nullable=False,
                      comment='存储键（文件路径）'),
            sa.Column('file_hash', sa.String(length=64), nullable=False,
                      comment='文件 SHA256 哈希'),
            sa.Column('original_name', sa.String(length=255), nullable=False,
                      comment='原始文件名'),
            sa.Column('file_type', sa.Enum('image', 'video', 'audio', 'document', 'other',
                                            name='filetype'),
                      nullable=False, comment='文件类型'),
            sa.Column('mime_type', sa.String(length=100), nullable=False,
                      comment='MIME 类型'),
            sa.Column('file_size', sa.BigInteger(), nullable=False,
                      comment='文件大小（字节）'),
            sa.Column('storage_backend', sa.Enum('local', 'minio', 's3', 'oss',
                                                  name='storagebackend'),
                      nullable=False, comment='存储后端'),
            sa.Column('bucket', sa.String(length=100), nullable=True,
                      comment='存储桶名称'),
            sa.Column('public_url', sa.String(length=512), nullable=True,
                      comment='公开访问 URL'),
            sa.Column('source_type', sa.String(length=50), nullable=False,
                      comment='来源类型'),
            sa.Column('source_id', sa.Integer(), nullable=False,
                      comment='来源记录 ID'),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            comment='存储文件元数据表'
        )
        op.create_index('ix_storage_files_id', 'storage_files', ['id'])
        op.create_index('ix_storage_files_file_key', 'storage_files',
                        ['file_key'], unique=True)
        op.create_index('ix_storage_files_file_hash', 'storage_files', ['file_hash'])
        op.create_index('ix_storage_files_file_type', 'storage_files', ['file_type'])
        op.create_index('ix_storage_files_storage_backend', 'storage_files', ['storage_backend'])
        op.create_index('ix_storage_files_source_type', 'storage_files', ['source_type'])
        op.create_index('ix_storage_files_source_id', 'storage_files', ['source_id'])
        op.create_index('idx_storage_source', 'storage_files', ['source_type', 'source_id'])
        op.create_index('idx_storage_type_created', 'storage_files',
                        ['file_type', 'created_at'])

    # =============================================================
    # 7. 创建 export_tasks 表
    # =============================================================
    if not table_exists('export_tasks'):
        op.create_table(
            'export_tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_id', sa.String(length=36), nullable=False,
                      comment='任务 UUID'),
            sa.Column('data_source', sa.String(length=50), nullable=False,
                      comment='数据源类型：news, social_sessions, social_messages'),
            sa.Column('export_format', sa.Enum('csv', 'json', 'excel',
                                                name='exportformat'),
                      nullable=False, comment='导出格式'),
            sa.Column('filters', sa.Text(), nullable=True,
                      comment='过滤条件（JSON）'),
            sa.Column('filename', sa.String(length=255), nullable=True,
                      comment='导出文件名'),
            sa.Column('status', sa.Enum('pending', 'processing', 'completed',
                                         'failed', 'expired', name='exportstatus'),
                      nullable=False, server_default='pending', comment='任务状态'),
            sa.Column('progress', sa.Integer(), nullable=False, server_default='0',
                      comment='进度百分比'),
            sa.Column('total_records', sa.Integer(), nullable=False, server_default='0',
                      comment='总记录数'),
            sa.Column('exported_records', sa.Integer(), nullable=False, server_default='0',
                      comment='已导出记录数'),
            sa.Column('file_key', sa.String(length=255), nullable=True,
                      comment='存储文件键'),
            sa.Column('file_path', sa.String(length=512), nullable=True,
                      comment='本地文件路径'),
            sa.Column('file_size', sa.Integer(), nullable=True,
                      comment='文件大小'),
            sa.Column('download_url', sa.String(length=512), nullable=True,
                      comment='下载 URL'),
            sa.Column('expires_at', sa.DateTime(), nullable=True,
                      comment='过期时间'),
            sa.Column('error_message', sa.Text(), nullable=True,
                      comment='错误信息'),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.func.now()),
            sa.Column('started_at', sa.DateTime(), nullable=True,
                      comment='开始时间'),
            sa.Column('completed_at', sa.DateTime(), nullable=True,
                      comment='完成时间'),
            sa.PrimaryKeyConstraint('id'),
            comment='数据导出任务表'
        )
        op.create_index('ix_export_tasks_id', 'export_tasks', ['id'])
        op.create_index('ix_export_tasks_task_id', 'export_tasks',
                        ['task_id'], unique=True)
        op.create_index('ix_export_tasks_data_source', 'export_tasks', ['data_source'])
        op.create_index('ix_export_tasks_status', 'export_tasks', ['status'])
        op.create_index('idx_export_status_created', 'export_tasks', ['status', 'created_at'])
        op.create_index('idx_source_status', 'export_tasks', ['data_source', 'status'])


def downgrade() -> None:
    # 删除 export_tasks 表
    op.drop_table('export_tasks')

    # 删除 storage_files 表
    op.drop_table('storage_files')

    # 删除 proxy_configs 表
    op.drop_table('proxy_configs')

    # 删除 account_credentials 表
    op.drop_table('account_credentials')

    # 删除 social_messages 表
    op.drop_table('social_messages')

    # 删除 social_sessions 表
    op.drop_table('social_sessions')

    # 恢复 news_articles 表
    op.drop_index('ix_news_articles_simhash', table_name='news_articles')
    op.drop_column('news_articles', 'simhash')
    op.drop_column('news_articles', 'content_text')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS exportstatus")
    op.execute("DROP TYPE IF EXISTS exportformat")
    op.execute("DROP TYPE IF EXISTS storagebackend")
    op.execute("DROP TYPE IF EXISTS filetype")
    op.execute("DROP TYPE IF EXISTS proxystatus")
    op.execute("DROP TYPE IF EXISTS proxyprotocol")
    op.execute("DROP TYPE IF EXISTS credentialstatus")
    op.execute("DROP TYPE IF EXISTS targettype")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
    op.execute("DROP TYPE IF EXISTS platform")
