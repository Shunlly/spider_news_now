"""Structured logging configuration."""

import logging
import sys
from typing import Any, Dict

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "source_key"):
            log_data["source_key"] = record.source_key
        if hasattr(record, "article_count"):
            log_data["article_count"] = record.article_count
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return str(log_data)


def setup_logging() -> None:
    """Configure application logging."""
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(
        StructuredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
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
