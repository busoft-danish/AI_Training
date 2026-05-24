from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from connectors.base_connector import BaseSourceConnector
from models.incident_model import IncidentRecord
from utils.exceptions import ConnectorError

log = structlog.get_logger(__name__)

# Left join so incidents without resolution notes are still included
FETCH_ALL_SQL = text("""
    SELECT
        i.incident_id,
        i.event_description,
        i.severity,
        i.resolved_at,
        i.status,
        r.response_steps,
        r.resolution,
        r.preventive_measures
    FROM safety_incidents i
    LEFT JOIN resolution_notes r ON i.incident_id = r.incident_id
""")

FETCH_SINCE_SQL = text("""
    SELECT
        i.incident_id,
        i.event_description,
        i.severity,
        i.resolved_at,
        i.status,
        r.response_steps,
        r.resolution,
        r.preventive_measures
    FROM safety_incidents i
    LEFT JOIN resolution_notes r ON i.incident_id = r.incident_id
    WHERE i.updated_at > :watermark
""")


class PostgresConnector(BaseSourceConnector):
    """Fetches incident records from PostgreSQL using async SQLAlchemy."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def fetch_all(self) -> list[dict[str, Any]]:
        """Fetch every incident joined with its resolution notes."""
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(FETCH_ALL_SQL)
                rows = result.mappings().all()
        except Exception as exc:
            raise ConnectorError(f"PostgreSQL fetch_all failed: {exc}") from exc

        return self._validate_rows(rows)

    async def fetch_since(self, watermark: datetime) -> list[dict[str, Any]]:
        """Fetch only incidents updated after the watermark timestamp."""
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(FETCH_SINCE_SQL, {"watermark": watermark})
                rows = result.mappings().all()
        except Exception as exc:
            raise ConnectorError(f"PostgreSQL fetch_since failed: {exc}") from exc

        return self._validate_rows(rows)

    def _validate_rows(self, rows: list) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for row in rows:
            raw = dict(row)
            try:
                incident = IncidentRecord(**raw)
                records.append(incident.model_dump())
            except Exception as exc:
                log.warning("postgres.row_skipped", reason=str(exc), row=raw)
        log.info("postgres.fetched", total=len(records))
        return records
