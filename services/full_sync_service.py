import structlog

from connectors.base_connector import BaseSourceConnector
from strategies.base_sync_strategy import BaseSyncStrategy
from services.sync_logger_service import SyncLoggerService, SyncStats

log = structlog.get_logger(__name__)


class FullSyncService:
    """Runs a full sync: fetch all records and process every one of them.

    Delegates change detection and upload to the injected strategy,
    so this service stays thin and strategy-agnostic.
    """

    def __init__(
        self,
        connector: BaseSourceConnector,
        strategy: BaseSyncStrategy,
        sync_logger: SyncLoggerService,
        entity_type: str,
    ) -> None:
        self._connector = connector
        self._strategy = strategy
        self._logger = sync_logger
        self._entity_type = entity_type

    async def run(self, run_id: str) -> SyncStats:
        """Execute a full sync and return statistics."""
        log.info("full_sync.started", entity_type=self._entity_type, run_id=run_id)
        records = await self._connector.fetch_all()

        if not records:
            log.warning("full_sync.empty_dataset", entity_type=self._entity_type)
            return SyncStats()

        stats = await self._strategy.process_records(records, self._entity_type, run_id)
        self._logger.log_summary(stats)
        log.info("full_sync.completed", entity_type=self._entity_type, run_id=run_id)
        return stats
