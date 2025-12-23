"""
Database Package - 数据库包（向后兼容层）

注意：此模块已迁移至 app.infrastructure.database
请在新代码中使用 from app.infrastructure.database import ...
"""

# 向后兼容导出
from app.infrastructure.database import (
    AsyncSessionLocal,
    Base,
    async_session_maker,
    engine,
    get_async_session,
    get_db,
)

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "async_session_maker",
    "get_db",
    "get_async_session",
]
