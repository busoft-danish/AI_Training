"""Unit tests for watermark-based sync strategy."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from datetime import datetime, timezone

from services.hash_service import HashService


@pytest.mark.asyncio
async def test_watermark_strategy_processes_new_incident():
    from strategies.watermark_sync_strategy import WatermarkSyncStrategy

    md_svc = MagicMock()
    md_svc.render.return_value = "# Incident I001"
    md_svc.save.return_value = Path("output/incidents/I001.md")

    upload_svc = MagicMock()
    manifest_svc = AsyncMock()
    manifest_svc.get.return_value = None  # NEW

    hash_svc = HashService()
    logger_svc = MagicMock()

    strategy = WatermarkSyncStrategy(
        markdown_service=md_svc,
        upload_service=upload_svc,
        manifest_service=manifest_svc,
        hash_service=hash_svc,
        sync_logger=logger_svc,
        source_type="postgres",
        s3_prefix="kidshuttle/incidents",
        entity_id_field="incident_id",
    )

    records = [{
        "incident_id": "I001", "event_description": "Child left on bus",
        "severity": "HIGH", "resolved_at": "2024-11-01", "status": "RESOLVED",
        "response_steps": "Assess", "resolution": "Resolved", "preventive_measures": "Checklist",
    }]

    stats = await strategy.process_records(records, "incident", "run-001")

    assert stats.new == 1
    assert stats.failed == 0
    upload_svc.upload.assert_called_once()
    manifest_svc.save.assert_called_once()


@pytest.mark.asyncio
async def test_watermark_strategy_marks_updated_incident():
    from strategies.watermark_sync_strategy import WatermarkSyncStrategy
    from models.manifest_model import ManifestEntry
    from utils.time_utils import utc_now

    existing = ManifestEntry(
        entity_type="incident", entity_id="I001", source_type="postgres",
        s3_key="kidshuttle/incidents/I001.md", content_hash="old", source_hash="old",
        generated_at=utc_now(), last_synced_at=utc_now(), sync_run_id="old", status="NEW",
    )

    md_svc = MagicMock()
    md_svc.render.return_value = "# Incident I001 Updated"
    md_svc.save.return_value = Path("output/incidents/I001.md")

    upload_svc = MagicMock()
    manifest_svc = AsyncMock()
    manifest_svc.get.return_value = existing  # UPDATED

    strategy = WatermarkSyncStrategy(
        markdown_service=md_svc,
        upload_service=upload_svc,
        manifest_service=manifest_svc,
        hash_service=HashService(),
        sync_logger=MagicMock(),
        source_type="postgres",
        s3_prefix="kidshuttle/incidents",
        entity_id_field="incident_id",
    )

    records = [{
        "incident_id": "I001", "event_description": "Updated description",
        "severity": "CRITICAL", "resolved_at": None, "status": "OPEN",
        "response_steps": "", "resolution": "", "preventive_measures": "",
    }]

    stats = await strategy.process_records(records, "incident", "run-002")

    assert stats.updated == 1
    assert stats.new == 0


@pytest.mark.asyncio
async def test_watermark_strategy_handles_upload_failure():
    from strategies.watermark_sync_strategy import WatermarkSyncStrategy
    from utils.exceptions import UploadError

    md_svc = MagicMock()
    md_svc.render.return_value = "# Incident I002"
    md_svc.save.return_value = Path("output/incidents/I002.md")

    upload_svc = MagicMock()
    upload_svc.upload.side_effect = UploadError("MinIO unreachable")

    manifest_svc = AsyncMock()
    manifest_svc.get.return_value = None

    strategy = WatermarkSyncStrategy(
        markdown_service=md_svc,
        upload_service=upload_svc,
        manifest_service=manifest_svc,
        hash_service=HashService(),
        sync_logger=MagicMock(),
        source_type="postgres",
        s3_prefix="kidshuttle/incidents",
        entity_id_field="incident_id",
    )

    records = [{
        "incident_id": "I002", "event_description": "Test", "severity": "LOW",
        "resolved_at": None, "status": "OPEN", "response_steps": "",
        "resolution": "", "preventive_measures": "",
    }]

    stats = await strategy.process_records(records, "incident", "run-003")

    assert stats.failed == 1
    assert stats.new == 0
