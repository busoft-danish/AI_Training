from sqlalchemy.ext.asyncio import AsyncEngine

from connectors.base_connector import BaseSourceConnector
from connectors.excel_connector import ExcelConnector
from connectors.postgres_connector import PostgresConnector
from utils.constants import SOURCE_EXCEL, SOURCE_POSTGRES


class ConnectorFactory:
    """Builds source connectors by type.

    Callers request a connector by name — they don't need to know
    which class or constructor arguments are involved.
    """

    def __init__(self, excel_path: str, pg_engine: AsyncEngine) -> None:
        self._excel_path = excel_path
        self._pg_engine = pg_engine

    def create(self, source_type: str) -> BaseSourceConnector:
        if source_type == SOURCE_EXCEL:
            return ExcelConnector(self._excel_path)
        if source_type == SOURCE_POSTGRES:
            return PostgresConnector(self._pg_engine)
        raise ValueError(f"Unknown source type: {source_type}")
