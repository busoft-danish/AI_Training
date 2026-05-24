import time
from dataclasses import dataclass, field

import structlog

log = structlog.get_logger(__name__)


@dataclass
class SyncStats:
    """Counters for one sync run."""
    new: int = 0
    updated: int = 0
    deleted: int = 0
    unchanged: int = 0
    failed: int = 0
    _start: float = field(default_factory=time.monotonic, repr=False)

    @property
    def duration_ms(self) -> int:
        return int((time.monotonic() - self._start) * 1000)


class SyncLoggerService:
    """Emits structured log events during a sync run."""

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id

    def log_action(self, action: str, entity_id: str, duration_ms: int = 0, **extra) -> None:
        log.info(
            "sync.action",
            correlation_id=self._run_id,
            entity_id=entity_id,
            action=action,
            duration_ms=duration_ms,
            **extra,
        )

    def log_failure(self, entity_id: str, error: str) -> None:
        log.error(
            "sync.failure",
            correlation_id=self._run_id,
            entity_id=entity_id,
            action="FAILED",
            error=error,
        )

    def log_summary(self, stats: SyncStats) -> None:
        log.info(
            "sync.summary",
            correlation_id=self._run_id,
            new=stats.new,
            updated=stats.updated,
            deleted=stats.deleted,
            unchanged=stats.unchanged,
            failed=stats.failed,
            duration_ms=stats.duration_ms,
        )
