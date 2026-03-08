from datetime import datetime

from pydantic import BaseModel


class IncidentOut(BaseModel):
    id: int
    upload_id: int
    fingerprint: str
    title: str | None = None
    severity: str
    count: int
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    sample_message: str | None = None
    sample_traceback: str | None = None
    ai_summary: str | None = None
    possible_causes: list[str] = []
    next_steps: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentListOut(BaseModel):
    incidents: list[IncidentOut]


class AISummary(BaseModel):
    title: str
    summary: str
    possible_causes: list[str]
    next_steps: list[str]
    severity: str
