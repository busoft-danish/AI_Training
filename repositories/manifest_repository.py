from datetime import datetime
from typing import Optional

import aiosqlite
import structlog

from models.manifest_model import ManifestEntry
from utils.exceptions import ManifestError

log = structlog.get_logger(__name__)


class ManifestRepository:
    """All CRUD operations against the SQLite manifest table.

    Injected with an aiosqlite connection so it's easy to swap in tests.
    """

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get(self, entity_type: str, entity_id: str) -> Optional[ManifestEntry]:
        """Fetch a single manifest entry, or None if it doesn't exist."""
        try:
            cursor = await self._conn.execute(
                "SELECT * FROM manifest WHERE entity_type = ? AND entity_id = ?",
                (entity_type, entity_id),
            )
            row = await cursor.fetchone()
            return self._row_to_entry(row) if row else None
        except Exception as exc:
            raise ManifestError(f"manifest.get failed: {exc}") from exc

    async def upsert(self, entry: ManifestEntry) -> None:
        """Insert or replace a manifest entry."""
        try:
            await self._conn.execute(
                """
                INSERT INTO manifest
                    (entity_type, entity_id, source_type, s3_key, content_hash,
                     source_hash, generated_at, last_synced_at, sync_run_id, status, watermark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                    source_type    = excluded.source_type,
                    s3_key         = excluded.s3_key,
                    content_hash   = excluded.content_hash,
                    source_hash    = excluded.source_hash,
                    generated_at   = excluded.generated_at,
                    last_synced_at = excluded.last_synced_at,
                    sync_run_id    = excluded.sync_run_id,
                    status         = excluded.status,
                    watermark      = excluded.watermark
                """,
                (
                    entry.entity_type, entry.entity_id, entry.source_type,
                    entry.s3_key, entry.content_hash, entry.source_hash,
                    entry.generated_at.isoformat(), entry.last_synced_at.isoformat(),
                    entry.sync_run_id, entry.status,
                    entry.watermark.isoformat() if entry.watermark else None,
                ),
            )
            await self._conn.commit()
        except Exception as exc:
            raise ManifestError(f"manifest.upsert failed: {exc}") from exc

    async def get_all_by_type(self, entity_type: str) -> list[ManifestEntry]:
        """Return all manifest entries for a given entity type."""
        try:
            cursor = await self._conn.execute(
                "SELECT * FROM manifest WHERE entity_type = ?", (entity_type,)
            )
            rows = await cursor.fetchall()
            return [self._row_to_entry(r) for r in rows]
        except Exception as exc:
            raise ManifestError(f"manifest.get_all_by_type failed: {exc}") from exc

    async def mark_deleted(self, entity_type: str, entity_id: str, run_id: str) -> None:
        """Mark an entity as DELETED in the manifest."""
        try:
            await self._conn.execute(
                "UPDATE manifest SET status = 'DELETED', sync_run_id = ? "
                "WHERE entity_type = ? AND entity_id = ?",
                (run_id, entity_type, entity_id),
            )
            await self._conn.commit()
        except Exception as exc:
            raise ManifestError(f"manifest.mark_deleted failed: {exc}") from exc

    async def get_latest_watermark(self, entity_type: str) -> Optional[datetime]:
        """Return the most recent watermark for watermark-based sync."""
        try:
            cursor = await self._conn.execute(
                "SELECT MAX(watermark) FROM manifest WHERE entity_type = ?",
                (entity_type,),
            )
            row = await cursor.fetchone()
            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None
        except Exception as exc:
            raise ManifestError(f"manifest.get_latest_watermark failed: {exc}") from exc

    @staticmethod
    def _row_to_entry(row: aiosqlite.Row) -> ManifestEntry:
        d = dict(row)
        return ManifestEntry(
            entity_type=d["entity_type"],
            entity_id=d["entity_id"],
            source_type=d["source_type"],
            s3_key=d["s3_key"],
            content_hash=d["content_hash"],
            source_hash=d["source_hash"],
            generated_at=datetime.fromisoformat(d["generated_at"]),
            last_synced_at=datetime.fromisoformat(d["last_synced_at"]),
            sync_run_id=d["sync_run_id"],
            status=d["status"],
            watermark=datetime.fromisoformat(d["watermark"]) if d.get("watermark") else None,
        )
