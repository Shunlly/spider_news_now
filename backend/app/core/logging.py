"""Structured logging configuration."""

import logging
import sys

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured log messages with clear timestamps."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp and structured data."""
        # Build extra info string
        extras = []
        if hasattr(record, "source_key"):
            extras.append(f"source={record.source_key}")
        if hasattr(record, "article_count"):
            extras.append(f"count={record.article_count}")
        if hasattr(record, "duration"):
            extras.append(f"duration={record.duration}s")

        # Format the base message
        base_msg = super().format(record)

        # Append extras if any
        if extras:
            base_msg += f" [{', '.join(extras)}]"

        return base_msg


def setup_logging() -> None:
    """Configure application logging."""
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Configure SQLAlchemy logger
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Configure APScheduler logger
    logging.getLogger("apscheduler").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("Starting scraper", extra={"source_key": "sina"})
        ```
    """
    return logging.getLogger(name)
