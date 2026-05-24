from typing import Any
from datetime import datetime

import pandas as pd
import structlog

from connectors.base_connector import BaseSourceConnector
from models.driver_model import DriverRecord
from utils.exceptions import ConnectorError, MissingColumnError

log = structlog.get_logger(__name__)

REQUIRED_COLUMNS = {"driver_id", "name", "license_expiry", "training_certs", "last_inspection_date"}


class ExcelConnector(BaseSourceConnector):
    """Reads driver records from an Excel file.

    Excel data has no updated_at column, so fetch_since falls back to fetch_all.
    Hash-based sync handles change detection for this source.
    """

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    async def fetch_all(self) -> list[dict[str, Any]]:
        """Load and validate all rows from the Excel file."""
        try:
            df = pd.read_excel(self._file_path, dtype=str)
        except FileNotFoundError:
            raise ConnectorError(f"Excel file not found: {self._file_path}")
        except Exception as exc:
            raise ConnectorError(f"Failed to read Excel file: {exc}") from exc

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise MissingColumnError(f"Missing columns in Excel: {missing}")

        df = df.where(pd.notna(df), None)
        records: list[dict[str, Any]] = []

        for _, row in df.iterrows():
            raw = row.to_dict()
            try:
                driver = DriverRecord(**raw)
                records.append(driver.model_dump())
            except Exception as exc:
                log.warning("excel.row_skipped", reason=str(exc), row=raw)

        log.info("excel.fetched", total=len(records))
        return records

    async def fetch_since(self, watermark: datetime) -> list[dict[str, Any]]:
        """Excel has no timestamps — always return all records."""
        return await self.fetch_all()
