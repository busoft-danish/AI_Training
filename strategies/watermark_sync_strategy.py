import time
from typing import Any
import structlog
from services.hash_service import HashService
from services.manifest_service import ManifestService
from services.markdown_service import MarkdownService
from services.upload_service import UploadService
from services.sync_logger_service import SyncLoggerService, SyncStats
from strategies.base_sync_strategy import BaseSyncStrategy
from utils.constants import STATUS_NEW, STATUS_UPDATED
from utils.time_utils import utc_now

log = structlog.get_logger(__name__)


class WatermarkSyncStrategy(BaseSyncStrategy):
    """Processes only records fetched after the last watermark timestamp.

    The connector already filters by updated_at > watermark, so this strategy
    just needs to render, upload, and update the manifest for each record.
    Deletion detection is not done here — use a periodic full sync for that.
    """

    def __init__(
        self,
        markdown_service: MarkdownService,
        upload_service: UploadService,
        manifest_service: ManifestService,
        hash_service: HashService,
        sync_logger: SyncLoggerService,
        source_type: str,
        s3_prefix: str,
        entity_id_field: str,
    ) -> None:
        self._md = markdown_service
        self._upload = upload_service
        self._manifest = manifest_service
        self._hash = hash_service
        self._logger = sync_logger
        self._source_type = source_type
        self._s3_prefix = s3_prefix
        self._entity_id_field = entity_id_field

    async def process_records(
        self,
        records: list[dict[str, Any]],
        entity_type: str,
        run_id: str,
    ) -> SyncStats:
        stats = SyncStats()
        watermark = utc_now()

        for record in records:
            entity_id = record[self._entity_id_field]
            t0 = time.monotonic()

            existing = await self._manifest.get(entity_type, entity_id)
            status = STATUS_NEW if existing is None else STATUS_UPDATED

            try:
                content = self._md.render(record)
                content_hash = self._hash.compute_content_hash(content)
                source_hash = self._hash.compute_source_hash(record)
                local_path = self._md.save(entity_id, content)
                s3_key = f"{self._s3_prefix}/{entity_id}.md"
                self._upload.upload(local_path, s3_key)

                await self._manifest.save(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    source_type=self._source_type,
                    s3_key=s3_key,
                    content_hash=content_hash,
                    source_hash=source_hash,
                    sync_run_id=run_id,
                    status=status,
                    watermark=watermark,
                )

                duration = int((time.monotonic() - t0) * 1000)
                self._logger.log_action(status, entity_id, duration_ms=duration)

                if status == STATUS_NEW:
                    stats.new += 1
                else:
                    stats.updated += 1

            except Exception as exc:
                stats.failed += 1
                self._logger.log_failure(entity_id, str(exc))

        return stats
