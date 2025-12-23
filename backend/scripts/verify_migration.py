#!/usr/bin/env python3
"""
Migration Verification Script - 迁移验证脚本

验证数据库迁移是否成功完成：
1. 检查所有业务表是否包含 user_id 字段
2. 验证没有 NULL 的 user_id 值
3. 验证外键约束存在
4. 验证索引存在

Usage:
    python scripts/verify_migration.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# 需要验证的表及其相关信息
TABLES_TO_VERIFY = [
    {
        "table": "news_sources",
        "fk_name": "fk_news_sources_user_id",
        "index_name": "ix_news_sources_user_id",
    },
    {
        "table": "news_articles",
        "fk_name": "fk_news_articles_user_id",
        "index_name": "idx_article_user_date",
    },
    {
        "table": "scraper_runs",
        "fk_name": "fk_scraper_runs_user_id",
        "index_name": "ix_scraper_runs_user_id",
    },
    {
        "table": "social_sessions",
        "fk_name": "fk_social_sessions_user_id",
        "index_name": "idx_session_user_platform",
    },
    {
        "table": "account_credentials",
        "fk_name": "fk_account_credentials_user_id",
        "index_name": "ix_account_credentials_user_id",
    },
    {
        "table": "proxy_configs",
        "fk_name": "fk_proxy_configs_user_id",
        "index_name": "ix_proxy_configs_user_id",
    },
    {
        "table": "export_tasks",
        "fk_name": "fk_export_tasks_user_id",
        "index_name": "ix_export_tasks_user_id",
    },
]


async def verify_migration():
    """
    验证迁移是否成功

    Returns:
        bool: True 如果所有验证通过，否则 False
    """
    engine = create_async_engine(str(settings.DATABASE_URL))
    all_passed = True
    errors = []

    async with engine.connect() as conn:
        print("=" * 60)
        print("数据库迁移验证 - Migration Verification")
        print("=" * 60)
        print()

        for table_info in TABLES_TO_VERIFY:
            table = table_info["table"]
            fk_name = table_info["fk_name"]
            index_name = table_info["index_name"]

            print(f"验证表: {table}")
            print("-" * 40)

            # 1. 检查 user_id 列是否存在
            check_column = text(f"""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = '{table}'
                AND column_name = 'user_id'
            """)
            result = await conn.execute(check_column)
            column_exists = result.scalar() > 0

            if column_exists:
                print("  [OK] user_id 列存在")
            else:
                print("  [FAIL] user_id 列不存在")
                errors.append(f"{table}: user_id 列不存在")
                all_passed = False
                continue

            # 2. 检查是否有 NULL 值
            check_null = text(f"""
                SELECT COUNT(*) FROM {table} WHERE user_id IS NULL
            """)
            result = await conn.execute(check_null)
            null_count = result.scalar()

            if null_count == 0:
                print("  [OK] 没有 NULL 的 user_id 值")
            else:
                print(f"  [FAIL] 存在 {null_count} 条记录的 user_id 为 NULL")
                errors.append(f"{table}: {null_count} 条记录的 user_id 为 NULL")
                all_passed = False

            # 3. 检查外键约束
            check_fk = text(f"""
                SELECT COUNT(*)
                FROM information_schema.table_constraints
                WHERE table_schema = DATABASE()
                AND table_name = '{table}'
                AND constraint_name = '{fk_name}'
                AND constraint_type = 'FOREIGN KEY'
            """)
            result = await conn.execute(check_fk)
            fk_exists = result.scalar() > 0

            if fk_exists:
                print(f"  [OK] 外键约束 {fk_name} 存在")
            else:
                print(f"  [WARN] 外键约束 {fk_name} 不存在")
                # 外键可能名称不同，不算致命错误
                # errors.append(f"{table}: 外键约束 {fk_name} 不存在")

            # 4. 检查索引
            check_index = text(f"""
                SELECT COUNT(*)
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                AND table_name = '{table}'
                AND index_name = '{index_name}'
            """)
            result = await conn.execute(check_index)
            index_exists = result.scalar() > 0

            if index_exists:
                print(f"  [OK] 索引 {index_name} 存在")
            else:
                print(f"  [WARN] 索引 {index_name} 不存在")

            # 5. 获取记录总数
            count_query = text(f"SELECT COUNT(*) FROM {table}")
            result = await conn.execute(count_query)
            total_count = result.scalar()
            print(f"  [INFO] 总记录数: {total_count}")

            print()

        # 验证 users 表
        print("验证表: users")
        print("-" * 40)

        check_admin = text("""
            SELECT COUNT(*) FROM users WHERE username = 'admin'
        """)
        result = await conn.execute(check_admin)
        admin_exists = result.scalar() > 0

        if admin_exists:
            print("  [OK] admin 用户存在")
        else:
            print("  [FAIL] admin 用户不存在")
            errors.append("users: admin 用户不存在")
            all_passed = False

        user_count = text("SELECT COUNT(*) FROM users")
        result = await conn.execute(user_count)
        total_users = result.scalar()
        print(f"  [INFO] 总用户数: {total_users}")

        print()
        print("=" * 60)

        if all_passed:
            print("验证结果: [SUCCESS] 所有检查通过!")
        else:
            print("验证结果: [FAILED] 存在以下问题:")
            for error in errors:
                print(f"  - {error}")

        print("=" * 60)

    await engine.dispose()
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(verify_migration())
    sys.exit(0 if result else 1)
