"""Utility helper functions."""

import hashlib
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Normalize a URL for consistent hashing.

    Normalizations applied:
    - Convert to lowercase
    - Remove trailing slashes
    - Sort query parameters
    - Remove common tracking parameters (utm_*, fbclid, etc.)

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL string
    """
    if not url:
        return ""

    # Parse the URL
    parsed = urlparse(url.lower().strip())

    # Remove trailing slash from path
    path = parsed.path.rstrip("/") or "/"

    # Sort and filter query parameters
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)

        # Remove tracking parameters
        tracking_params = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "ref", "source", "from"
        }
        filtered_params = {
            k: v for k, v in params.items()
            if k.lower() not in tracking_params
        }

        # Sort parameters and flatten single-value lists
        sorted_params = sorted(
            (k, v[0] if len(v) == 1 else v)
            for k, v in filtered_params.items()
        )
        query = urlencode(sorted_params, doseq=True)
    else:
        query = ""

    # Rebuild URL without fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        "",  # params
        query,
        ""   # fragment
    ))

    return normalized


def compute_url_hash(url: str) -> str:
    """
    Compute a hash for a URL for duplicate detection.

    Uses normalized URL to ensure consistent hashing.

    Args:
        url: The URL to hash

    Returns:
        SHA-256 hash of the normalized URL (first 32 chars)
    """
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def format_datetime(
    dt: datetime | None,
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str | None:
    """
    Format a datetime object to string.

    Args:
        dt: Datetime object to format
        format_str: Format string (default: ISO-like format)

    Returns:
        Formatted string or None if dt is None
    """
    if dt is None:
        return None
    return dt.strftime(format_str)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to append if truncated

    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
