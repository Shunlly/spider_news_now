"""Structured logging configuration."""

import logging
import re
import sys

from app.core.config import settings

# 敏感字段模式 - 用于过滤日志中的敏感数据
SENSITIVE_PATTERNS = [
    (re.compile(r'(password["\']?\s*[:=]\s*["\']?)[^"\'}\s,]+', re.IGNORECASE), r'\1***'),
    (re.compile(r'(token["\']?\s*[:=]\s*["\']?)[^"\'}\s,]+', re.IGNORECASE), r'\1***'),
    (re.compile(r'(secret["\']?\s*[:=]\s*["\']?)[^"\'}\s,]+', re.IGNORECASE), r'\1***'),
    (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\']?)[^"\'}\s,]+', re.IGNORECASE), r'\1***'),
    (re.compile(r'(authorization["\']?\s*[:=]\s*["\']?)[^"\'}\s,]+', re.IGNORECASE), r'\1***'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9_-]+\.?[A-Za-z0-9_-]*\.?[A-Za-z0-9_-]*', re.IGNORECASE), r'\1***'),
]


def sanitize_message(message: str) -> str:
    """
    过滤日志消息中的敏感数据

    Args:
        message: 原始日志消息

    Returns:
        脱敏后的日志消息
    """
    result = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class SensitiveDataFilter(logging.Filter):
    """
    敏感数据过滤器

    过滤日志记录中的密码、Token 等敏感信息
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤敏感数据"""
        # 过滤消息
        if isinstance(record.msg, str):
            record.msg = sanitize_message(record.msg)

        # 过滤 args
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(sanitize_message(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)

        return True


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

    # Add sensitive data filter to sanitize passwords, tokens, etc.
    console_handler.addFilter(SensitiveDataFilter())

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
