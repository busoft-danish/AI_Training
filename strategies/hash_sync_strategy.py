import time
from pathlib import Path
from typing import Any

import structlog

from services.hash_service import HashService
from services.manifest_service import ManifestService
from services.markdown_service import MarkdownService
from services.upload_service import UploadService
from services.sync_logger_service import SyncLoggerService, SyncStats
from strategies.base_sync_strategy import BaseSyncStrategy
from utils.constants import STATUS_NEW, STATUS_UPDATED, STATUS_UNCHANGED, STATUS_DELETED

log = structlog.get_logger(__name__)


class HashSyncStrategy(BaseSyncStrategy):
    """Detects changes by comparing SHA-256 hashes of source records.

    Best suited for Excel data that has no updated_at timestamp.
    Steps:
      1. Hash each incoming record.
      2. Compare against stored source_hash in manifest.
      3. Process only NEW or UPDATED records.
      4. Mark records missing from source as DELETED.
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
        incoming_ids: set[str] = set()

        for record in records:
            entity_id = record[self._entity_id_field]
            incoming_ids.add(entity_id)
            t0 = time.monotonic()

            source_hash = self._hash.compute_source_hash(record)
            existing = await self._manifest.get(entity_type, entity_id)

            if existing and not self._hash.has_changed(source_hash, existing.source_hash):
                stats.unchanged += 1
                self._logger.log_action(STATUS_UNCHANGED, entity_id)
                continue

            status = STATUS_NEW if existing is None else STATUS_UPDATED

            try:
                content = self._md.render(record)
                content_hash = self._hash.compute_content_hash(content)
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

        # Detect deletions — IDs in manifest but not in source
        known_ids = await self._manifest.get_all_ids(entity_type)
        for deleted_id in known_ids - incoming_ids:
            try:
                s3_key = f"{self._s3_prefix}/{deleted_id}.md"
                self._upload.delete(s3_key)
                await self._manifest.mark_deleted(entity_type, deleted_id, run_id)
                self._logger.log_action(STATUS_DELETED, deleted_id)
                stats.deleted += 1
            except Exception as exc:
                stats.failed += 1
                self._logger.log_failure(deleted_id, str(exc))

        return stats
