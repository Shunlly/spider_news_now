"""APScheduler configuration for task scheduling."""

from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level scheduler instance
_scheduler: AsyncScheduler | None = None


async def get_scheduler() -> AsyncScheduler:
    """
    Get or create the scheduler instance.

    Returns:
        AsyncScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        datastore = SQLAlchemyDataStore(settings.SCHEDULER_JOBSTORE_URL)
        _scheduler = AsyncScheduler(datastore)
    return _scheduler
