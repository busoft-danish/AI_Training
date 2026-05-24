import structlog

from connectors.base_connector import BaseSourceConnector
from strategies.base_sync_strategy import BaseSyncStrategy
from services.manifest_service import ManifestService
from services.sync_logger_service import SyncLoggerService, SyncStats

log = structlog.get_logger(__name__)


class IncrementalSyncService:
    """Runs an incremental sync using the last watermark from the manifest.

    For hash-based sources (Excel), the connector returns all records and
    the strategy skips unchanged ones. For watermark-based sources (Postgres),
    the connector filters at the DB level.
    """

    def __init__(
        self,
        connector: BaseSourceConnector,
        strategy: BaseSyncStrategy,
        manifest_service: ManifestService,
        sync_logger: SyncLoggerService,
        entity_type: str,
    ) -> None:
        self._connector = connector
        self._strategy = strategy
        self._manifest = manifest_service
        self._logger = sync_logger
        self._entity_type = entity_type

    async def run(self, run_id: str) -> SyncStats:
        """Execute an incremental sync and return statistics."""
        log.info("incremental_sync.started", entity_type=self._entity_type, run_id=run_id)

        watermark = await self._manifest.get_latest_watermark(self._entity_type)
        log.info("incremental_sync.watermark", watermark=str(watermark))

        records = await self._connector.fetch_since(watermark)

        if not records:
            log.info("incremental_sync.nothing_to_process", entity_type=self._entity_type)
            return SyncStats()

        stats = await self._strategy.process_records(records, self._entity_type, run_id)
        self._logger.log_summary(stats)
        log.info("incremental_sync.completed", entity_type=self._entity_type, run_id=run_id)
        return stats
