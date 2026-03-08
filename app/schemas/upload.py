from datetime import datetime

from pydantic import BaseModel


class UploadOut(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime
    processed_at: datetime | None = None
    total_lines: int
    total_events: int
    total_incidents: int
    error_message: str | None = None

    model_config = {"from_attributes": True}


class UploadListOut(BaseModel):
    uploads: list[UploadOut]
