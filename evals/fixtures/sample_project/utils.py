"""Utility functions for the sample project."""

from datetime import datetime


def format_date(dt: datetime) -> str:
    """Format a datetime as YYYY-MM-DD."""
    return dt.strftime("%Y-%m-%d")


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    return text.lower().replace(" ", "-").strip("-")


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
