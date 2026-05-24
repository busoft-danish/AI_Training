import asyncio
import sys
import structlog

from config.settings import get_settings
from controllers.sync_controller import SyncController
from database.sqlite import get_sqlite_connection
from factories.service_factory import ServiceFactory


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


async def main(mode: str) -> None:
    configure_logging()
    log = structlog.get_logger(__name__)

    settings = get_settings()
    sqlite_conn = await get_sqlite_connection(settings.sqlite_db_path)

    try:
        factory = ServiceFactory(settings, sqlite_conn)
        controller = SyncController(factory)

        if mode == "full":
            await controller.run_full_sync()
        elif mode == "incremental":
            await controller.run_incremental_sync()
        else:
            log.error("main.invalid_mode", mode=mode, hint="Use: full | incremental")
            sys.exit(1)
    finally:
        await sqlite_conn.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    asyncio.run(main(mode))
