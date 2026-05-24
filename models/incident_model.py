from pydantic import BaseModel, field_validator
from typing import Optional


class IncidentRecord(BaseModel):
    """Represents a joined row from safety_incidents + resolution_notes."""

    incident_id: str
    event_description: Optional[str] = ""
    severity: Optional[str] = ""
    resolved_at: Optional[str] = ""
    status: Optional[str] = ""
    response_steps: Optional[str] = ""
    resolution: Optional[str] = ""
    preventive_measures: Optional[str] = ""

    @field_validator("incident_id", mode="before")
    @classmethod
    def must_not_be_empty(cls, v: object) -> str:
        if not v or str(v).strip() == "":
            raise ValueError("incident_id is required")
        return str(v).strip()

    @field_validator(
        "event_description", "severity", "resolved_at", "status",
        "response_steps", "resolution", "preventive_measures",
        mode="before",
    )
    @classmethod
    def coerce_to_str(cls, v: object) -> str:
        return "" if v is None else str(v).strip()
