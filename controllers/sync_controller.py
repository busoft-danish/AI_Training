import structlog

from factories.service_factory import ServiceFactory

log = structlog.get_logger(__name__)


class SyncController:
    """Orchestrates full and incremental sync runs for all entity types.

    Composes services via the factory — no business logic lives here.
    Adding a new entity type only requires adding a method here and
    registering it in the factory.
    """

    def __init__(self, factory: ServiceFactory) -> None:
        self._factory = factory

    async def run_full_sync(self) -> None:
        """Run full sync for drivers (Excel) and incidents (PostgreSQL)."""
        log.info("controller.full_sync.started")

        driver_sync = self._factory.build_driver_full_sync()
        await driver_sync.run(run_id="full-drivers")

        incident_sync = self._factory.build_incident_full_sync()
        await incident_sync.run(run_id="full-incidents")

        log.info("controller.full_sync.completed")

    async def run_incremental_sync(self) -> None:
        """Run incremental sync for drivers (hash) and incidents (watermark)."""
        log.info("controller.incremental_sync.started")

        driver_sync = self._factory.build_driver_incremental_sync()
        await driver_sync.run(run_id="incr-drivers")

        incident_sync = self._factory.build_incident_incremental_sync()
        await incident_sync.run(run_id="incr-incidents")

        log.info("controller.incremental_sync.completed")
