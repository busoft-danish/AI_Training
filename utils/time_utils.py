from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert a naive datetime to UTC-aware. Assumes naive = UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
