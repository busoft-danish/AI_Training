from datetime import datetime
from typing import Optional

from models.manifest_model import ManifestEntry
from repositories.manifest_repository import ManifestRepository
from utils.constants import STATUS_DELETED
from utils.time_utils import utc_now


class ManifestService:
    """Business logic around manifest entries.

    Wraps the repository so callers don't build ManifestEntry objects themselves.
    """

    def __init__(self, repo: ManifestRepository) -> None:
        self._repo = repo

    async def get(self, entity_type: str, entity_id: str) -> Optional[ManifestEntry]:
        return await self._repo.get(entity_type, entity_id)

    async def save(
        self,
        entity_type: str,
        entity_id: str,
        source_type: str,
        s3_key: str,
        content_hash: str,
        source_hash: str,
        sync_run_id: str,
        status: str,
        watermark: Optional[datetime] = None,
    ) -> None:
        now = utc_now()
        entry = ManifestEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            source_type=source_type,
            s3_key=s3_key,
            content_hash=content_hash,
            source_hash=source_hash,
            generated_at=now,
            last_synced_at=now,
            sync_run_id=sync_run_id,
            status=status,
            watermark=watermark,
        )
        await self._repo.upsert(entry)

    async def mark_deleted(self, entity_type: str, entity_id: str, run_id: str) -> None:
        await self._repo.mark_deleted(entity_type, entity_id, run_id)

    async def get_all_ids(self, entity_type: str) -> set[str]:
        """Return the set of entity IDs currently tracked in the manifest."""
        entries = await self._repo.get_all_by_type(entity_type)
        return {e.entity_id for e in entries if e.status != STATUS_DELETED}

    async def get_latest_watermark(self, entity_type: str) -> Optional[datetime]:
        return await self._repo.get_latest_watermark(entity_type)
