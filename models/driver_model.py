from pydantic import BaseModel, field_validator
from typing import Optional


class DriverRecord(BaseModel):
    """Represents one row from drivers.xlsx after validation."""

    driver_id: str
    name: str
    license_expiry: str
    training_certs: Optional[str] = ""
    last_inspection_date: Optional[str] = ""

    @field_validator("driver_id", "name", mode="before")
    @classmethod
    def must_not_be_empty(cls, v: object) -> str:
        if not v or str(v).strip() == "":
            raise ValueError("driver_id and name are required fields")
        return str(v).strip()

    @field_validator("license_expiry", "training_certs", "last_inspection_date", mode="before")
    @classmethod
    def coerce_to_str(cls, v: object) -> str:
        return "" if v is None else str(v).strip()
