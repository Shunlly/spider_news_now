"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.models.role import Role, RoleType
from app.models.user import User

# Test database URL (use separate test database)
# Docker container exposes MySQL on port 33060
TEST_DATABASE_URL = "mysql+aiomysql://news_user:news_password@localhost:33060/news_scraper_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Create a test-specific app without scheduler (to avoid lifespan hanging)
@asynccontextmanager
async def test_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Minimal lifespan for tests - no scheduler initialization."""
    yield


def create_test_app() -> FastAPI:
    """Create a test FastAPI app without scheduler and middlewares."""
    from app.api.v1.router import api_router
    # Note: We skip both RateLimitMiddleware and TenantMiddleware for tests
    # - RateLimitMiddleware causes rate limit errors in tests
    # - TenantMiddleware tries to connect to production database

    test_app = FastAPI(
        title="Test App",
        lifespan=test_lifespan,
    )

    # Add CORS middleware only
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    test_app.include_router(api_router, prefix="/api/v1")

    return test_app


# Global test app instance
test_app = create_test_app()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Creates all tables before test and drops them after.
    """
    # Drop all tables first to ensure clean state
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, test_user: User) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Overrides the get_db dependency to use test database.
    Includes authentication token for API access.
    Uses test_app without scheduler to avoid lifespan hanging.
    """

    async def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    # Generate JWT token for test user
    access_token = create_access_token(subject=test_user.id)
    headers = {"Authorization": f"Bearer {access_token}"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac

    test_app.dependency_overrides.clear()


# Test user fixture - creates a user with role for testing
TEST_USER_ID = "test-user-00000000-0000-0000-0001"


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with role for foreign key references."""
    # Create role first
    role = Role(
        id=3,
        name=RoleType.USER.value,
        display_name="普通用户",
        permissions=["task:read", "task:create"],
    )
    db_session.add(role)
    await db_session.flush()

    # Create user
    user = User(
        id=TEST_USER_ID,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$test_hash_placeholder_value",
        role_id=role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


# Test data factories
@pytest.fixture
def sample_news_source(test_user):
    """Factory for creating sample news source data."""
    return {
        "user_id": test_user.id,
        "source_key": "test_source",
        "display_name": "Test News Source",
        "enabled": True,
        "scraper_module": "app.scrapers.test_scraper",
        "schedule_interval": 1800,
    }


@pytest.fixture
def sample_news_article(test_user):
    """Factory for creating sample news article data."""
    from datetime import datetime

    return {
        "user_id": test_user.id,
        "url": "https://test.example.com/article/123",
        "url_hash": "a" * 64,  # 64-char SHA-256 hash
        "title": "Test Article Title",
        "source_key": "test_source",
        "category": "test",
        "published_at": datetime.now(),
    }


@pytest.fixture
def sample_scraper_run():
    """Factory for creating sample scraper run data."""
    from datetime import datetime

    return {
        "source_key": "test_source",
        "started_at": datetime.now(),
        "status": "running",
        "articles_scraped": 0,
        "articles_new": 0,
        "articles_duplicate": 0,
    }


@pytest.fixture
def sample_credential():
    """Factory for creating sample credential data."""
    return {
        "name": "Test Credential",
        "platform": "twitter",
        "credentials": {"bearer_token": "test_token_12345"},
        "is_default": False,
    }


@pytest.fixture
def sample_proxy():
    """Factory for creating sample proxy data."""
    return {
        "name": "Test Proxy",
        "protocol": "http",
        "host": "proxy.example.com",
        "port": 8080,
        "username": "user",
        "password": "pass",
        "weight": 1,
        "priority": 0,
    }


@pytest.fixture
def sample_social_session():
    """Factory for creating sample social session data."""
    return {
        "platform": "twitter",
        "target_type": "user",
        "target_id": "123456789",
        "target_name": "Test User",
        "target_username": "testuser",
        "description": "Test session",
        "fetch_interval": 3600,
    }


@pytest.fixture
def sample_export_request():
    """Factory for creating sample export request data."""
    return {
        "data_source": "news",
        "export_format": "csv",
        "filters": {"source_key": "test_source"},
    }
