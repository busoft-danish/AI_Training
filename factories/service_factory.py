import aiosqlite

from config.settings import Settings
from connectors.base_connector import BaseSourceConnector
from database.postgres import create_postgres_engine
from factories.connector_factory import ConnectorFactory
from renderers.renderer_factory import RendererFactory
from repositories.manifest_repository import ManifestRepository
from services.full_sync_service import FullSyncService
from services.hash_service import HashService
from services.incremental_sync_service import IncrementalSyncService
from services.manifest_service import ManifestService
from services.markdown_service import MarkdownService
from services.sync_logger_service import SyncLoggerService
from services.upload_service import UploadService
from strategies.hash_sync_strategy import HashSyncStrategy
from strategies.watermark_sync_strategy import WatermarkSyncStrategy
from utils.constants import (
    ENTITY_DRIVER, ENTITY_INCIDENT,
    SOURCE_EXCEL, SOURCE_POSTGRES,
    MINIO_PREFIX_DRIVERS, MINIO_PREFIX_INCIDENTS,
    OUTPUT_DRIVERS, OUTPUT_INCIDENTS,
)
from utils.helper import new_run_id


class ServiceFactory:
    """Composition root — builds and wires all services.

    This is the only place that knows about concrete implementations.
    Everything else depends on abstractions.
    """

    def __init__(self, settings: Settings, sqlite_conn: aiosqlite.Connection) -> None:
        self._settings = settings
        self._sqlite_conn = sqlite_conn
        self._pg_engine = create_postgres_engine(settings.postgres_dsn)

        self._manifest_repo = ManifestRepository(sqlite_conn)
        self._manifest_svc = ManifestService(self._manifest_repo)
        self._hash_svc = HashService()
        self._upload_svc = UploadService(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
        )
        self._renderer_factory = RendererFactory(template_dir="templates")
        self._connector_factory = ConnectorFactory(
            excel_path=settings.excel_file_path,
            pg_engine=self._pg_engine,
        )

    def _make_markdown_service(self, entity_type: str, output_dir: str) -> MarkdownService:
        renderer = self._renderer_factory.create(entity_type)
        return MarkdownService(renderer, output_dir)

    def _make_hash_strategy(
        self, entity_type: str, source_type: str, s3_prefix: str,
        output_dir: str, entity_id_field: str, run_id: str,
    ) -> HashSyncStrategy:
        return HashSyncStrategy(
            markdown_service=self._make_markdown_service(entity_type, output_dir),
            upload_service=self._upload_svc,
            manifest_service=self._manifest_svc,
            hash_service=self._hash_svc,
            sync_logger=SyncLoggerService(run_id),
            source_type=source_type,
            s3_prefix=s3_prefix,
            entity_id_field=entity_id_field,
        )

    def _make_watermark_strategy(
        self, entity_type: str, source_type: str, s3_prefix: str,
        output_dir: str, entity_id_field: str, run_id: str,
    ) -> WatermarkSyncStrategy:
        return WatermarkSyncStrategy(
            markdown_service=self._make_markdown_service(entity_type, output_dir),
            upload_service=self._upload_svc,
            manifest_service=self._manifest_svc,
            hash_service=self._hash_svc,
            sync_logger=SyncLoggerService(run_id),
            source_type=source_type,
            s3_prefix=s3_prefix,
            entity_id_field=entity_id_field,
        )

    def build_driver_full_sync(self) -> FullSyncService:
        run_id = new_run_id()
        connector = self._connector_factory.create(SOURCE_EXCEL)
        strategy = self._make_hash_strategy(
            ENTITY_DRIVER, SOURCE_EXCEL, MINIO_PREFIX_DRIVERS,
            OUTPUT_DRIVERS, "driver_id", run_id,
        )
        return FullSyncService(connector, strategy, SyncLoggerService(run_id), ENTITY_DRIVER)

    def build_incident_full_sync(self) -> FullSyncService:
        run_id = new_run_id()
        connector = self._connector_factory.create(SOURCE_POSTGRES)
        strategy = self._make_watermark_strategy(
            ENTITY_INCIDENT, SOURCE_POSTGRES, MINIO_PREFIX_INCIDENTS,
            OUTPUT_INCIDENTS, "incident_id", run_id,
        )
        return FullSyncService(connector, strategy, SyncLoggerService(run_id), ENTITY_INCIDENT)

    def build_driver_incremental_sync(self) -> IncrementalSyncService:
        run_id = new_run_id()
        connector = self._connector_factory.create(SOURCE_EXCEL)
        strategy = self._make_hash_strategy(
            ENTITY_DRIVER, SOURCE_EXCEL, MINIO_PREFIX_DRIVERS,
            OUTPUT_DRIVERS, "driver_id", run_id,
        )
        return IncrementalSyncService(
            connector, strategy, self._manifest_svc, SyncLoggerService(run_id), ENTITY_DRIVER
        )

    def build_incident_incremental_sync(self) -> IncrementalSyncService:
        run_id = new_run_id()
        connector = self._connector_factory.create(SOURCE_POSTGRES)
        strategy = self._make_watermark_strategy(
            ENTITY_INCIDENT, SOURCE_POSTGRES, MINIO_PREFIX_INCIDENTS,
            OUTPUT_INCIDENTS, "incident_id", run_id,
        )
        return IncrementalSyncService(
            connector, strategy, self._manifest_svc, SyncLoggerService(run_id), ENTITY_INCIDENT
        )
