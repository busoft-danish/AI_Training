from abc import ABC, abstractmethod
from typing import Any

from services.sync_logger_service import SyncStats


class BaseSyncStrategy(ABC):
    """Defines the contract for a sync strategy.

    Concrete strategies (hash-based, watermark-based) implement process_records
    differently but are interchangeable from the caller's perspective.
    """

    @abstractmethod
    async def process_records(
        self,
        records: list[dict[str, Any]],
        entity_type: str,
        run_id: str,
    ) -> SyncStats:
        """Process a batch of records and return sync statistics."""
