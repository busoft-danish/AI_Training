"""Unit tests for hash-based sync strategy."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from services.hash_service import HashService
from utils.helper import generate_hash


# --- HashService unit tests ---

def test_compute_source_hash_is_deterministic():
    svc = HashService()
    record = {"driver_id": "D001", "name": "Alice"}
    assert svc.compute_source_hash(record) == svc.compute_source_hash(record)


def test_compute_source_hash_changes_on_data_change():
    svc = HashService()
    r1 = {"driver_id": "D001", "name": "Alice"}
    r2 = {"driver_id": "D001", "name": "Alice Updated"}
    assert svc.compute_source_hash(r1) != svc.compute_source_hash(r2)


def test_has_changed_returns_true_when_different():
    svc = HashService()
    assert svc.has_changed("abc", "xyz") is True


def test_has_changed_returns_false_when_same():
    svc = HashService()
    assert svc.has_changed("abc", "abc") is False


def test_compute_content_hash_differs_from_source_hash():
    svc = HashService()
    record = {"driver_id": "D001", "name": "Alice"}
    source_hash = svc.compute_source_hash(record)
    content_hash = svc.compute_content_hash("# Driver D001\n- Name: Alice")
    assert source_hash != content_hash


# --- Hash strategy: NEW record flow ---

@pytest.mark.asyncio
async def test_hash_strategy_processes_new_record():
    from strategies.hash_sync_strategy import HashSyncStrategy
    from utils.constants import STATUS_NEW

    md_svc = MagicMock()
    md_svc.render.return_value = "# Driver D001"
    md_svc.save.return_value = Path("output/drivers/D001.md")

    upload_svc = MagicMock()
    manifest_svc = AsyncMock()
    manifest_svc.get.return_value = None  # No existing entry = NEW
    manifest_svc.get_all_ids.return_value = set()

    hash_svc = HashService()
    logger_svc = MagicMock()
    logger_svc.log_action = MagicMock()
    logger_svc.log_failure = MagicMock()

    strategy = HashSyncStrategy(
        markdown_service=md_svc,
        upload_service=upload_svc,
        manifest_service=manifest_svc,
        hash_service=hash_svc,
        sync_logger=logger_svc,
        source_type="excel",
        s3_prefix="kidshuttle/drivers",
        entity_id_field="driver_id",
    )

    records = [{"driver_id": "D001", "name": "Alice", "license_expiry": "2025-12-01",
                "training_certs": "CPR", "last_inspection_date": "2024-11-01"}]

    stats = await strategy.process_records(records, "driver", "run-001")

    assert stats.new == 1
    assert stats.updated == 0
    assert stats.failed == 0
    upload_svc.upload.assert_called_once()
    manifest_svc.save.assert_called_once()


@pytest.mark.asyncio
async def test_hash_strategy_skips_unchanged_record():
    from strategies.hash_sync_strategy import HashSyncStrategy
    from models.manifest_model import ManifestEntry
    from utils.time_utils import utc_now

    record = {"driver_id": "D001", "name": "Alice", "license_expiry": "2025-12-01",
              "training_certs": "CPR", "last_inspection_date": "2024-11-01"}

    hash_svc = HashService()
    stored_hash = hash_svc.compute_source_hash(record)

    existing_entry = ManifestEntry(
        entity_type="driver", entity_id="D001", source_type="excel",
        s3_key="kidshuttle/drivers/D001.md", content_hash="abc", source_hash=stored_hash,
        generated_at=utc_now(), last_synced_at=utc_now(), sync_run_id="old-run", status="NEW",
    )

    md_svc = MagicMock()
    upload_svc = MagicMock()
    manifest_svc = AsyncMock()
    manifest_svc.get.return_value = existing_entry
    manifest_svc.get_all_ids.return_value = {"D001"}
    logger_svc = MagicMock()

    strategy = HashSyncStrategy(
        markdown_service=md_svc, upload_service=upload_svc,
        manifest_service=manifest_svc, hash_service=hash_svc,
        sync_logger=logger_svc, source_type="excel",
        s3_prefix="kidshuttle/drivers", entity_id_field="driver_id",
    )

    stats = await strategy.process_records([record], "driver", "run-002")

    assert stats.unchanged == 1
    upload_svc.upload.assert_not_called()
