"""
Async Database Session Management - 异步数据库会话管理

提供 SQLAlchemy 异步引擎和会话工厂。

使用连接池配置：
- pool_size: 20 常驻连接
- max_overflow: 40 最大额外连接
- pool_pre_ping: 连接使用前验证
- pool_recycle: 3600秒回收连接
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# 创建异步引擎（带连接池）
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.LOG_LEVEL == "DEBUG",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 后台任务别名
async_session_maker = AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入函数 - 获取数据库会话

    Yields:
        AsyncSession: 数据库会话，自动提交/回滚/关闭

    Example:
        ```python
        @app.get("/articles")
        async def get_articles(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(NewsArticle))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 别名，保持向后兼容
get_async_session = get_db
