from typing import Any
from utils.helper import generate_hash


class HashService:
    """Computes and compares content hashes for change detection."""

    def compute_source_hash(self, record: dict[str, Any]) -> str:
        """Hash the raw source record to detect data changes."""
        return generate_hash(record)

    def compute_content_hash(self, markdown: str) -> str:
        """Hash the rendered markdown to detect content changes."""
        import hashlib
        return hashlib.sha256(markdown.encode("utf-8")).hexdigest()

    def has_changed(self, new_hash: str, stored_hash: str) -> bool:
        """Return True if the hashes differ."""
        return new_hash != stored_hash
