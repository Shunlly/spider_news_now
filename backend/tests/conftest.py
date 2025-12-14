"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# Test database URL (use separate test database)
TEST_DATABASE_URL = "mysql+aiomysql://news_user:news_password@localhost:3306/news_scraper_test"

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
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Overrides the get_db dependency to use test database.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Test data factories
@pytest.fixture
def sample_news_source():
    """Factory for creating sample news source data."""
    return {
        "source_key": "test_source",
        "display_name": "Test News Source",
        "enabled": True,
        "scraper_module": "app.scrapers.test_scraper",
        "schedule_interval": 1800,
    }


@pytest.fixture
def sample_news_article():
    """Factory for creating sample news article data."""
    from datetime import datetime

    return {
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
