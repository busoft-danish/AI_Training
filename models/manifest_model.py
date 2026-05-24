from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ManifestEntry:
    """One row in the manifest table. Tracks sync state per entity."""

    entity_type: str
    entity_id: str
    source_type: str
    s3_key: str
    content_hash: str
    source_hash: str
    generated_at: datetime
    last_synced_at: datetime
    sync_run_id: str
    status: str
    watermark: Optional[datetime] = None
