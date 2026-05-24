import aiosqlite
from pathlib import Path


CREATE_MANIFEST_SQL = """
CREATE TABLE IF NOT EXISTS manifest (
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    source_type     TEXT NOT NULL,
    s3_key          TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    source_hash     TEXT NOT NULL,
    generated_at    DATETIME NOT NULL,
    last_synced_at  DATETIME NOT NULL,
    sync_run_id     TEXT NOT NULL,
    status          TEXT NOT NULL,
    watermark       DATETIME,
    PRIMARY KEY (entity_type, entity_id)
);
"""


async def get_sqlite_connection(db_path: str) -> aiosqlite.Connection:
    """Open an aiosqlite connection and ensure the manifest table exists."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute(CREATE_MANIFEST_SQL)
    await conn.commit()
    return conn
