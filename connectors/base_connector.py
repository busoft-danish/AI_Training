from abc import ABC, abstractmethod
from typing import Any


class BaseSourceConnector(ABC):
    """Abstract contract every source connector must satisfy.

    Keeping it to a single fetch method respects ISP — connectors
    that don't need extra methods won't be forced to implement them.
    """

    @abstractmethod
    async def fetch_all(self) -> list[dict[str, Any]]:
        """Return all records from the source as plain dicts."""

    @abstractmethod
    async def fetch_since(self, watermark: Any) -> list[dict[str, Any]]:
        """Return only records changed after the given watermark."""
