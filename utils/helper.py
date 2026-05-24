import hashlib
import uuid
from typing import Any


def generate_hash(data: dict[str, Any]) -> str:
    """SHA-256 hash of a dict's string representation. Used for change detection."""
    raw = str(sorted(data.items())).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def new_run_id() -> str:
    """Generate a unique sync run ID."""
    return str(uuid.uuid4())


def safe_str(value: Any) -> str:
    """Convert any value to string, returning empty string for None."""
    return "" if value is None else str(value)
