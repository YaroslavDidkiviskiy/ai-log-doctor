from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    upload_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("uploads.id"), nullable=False, index=True
    )
    fingerprint: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sample_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    possible_causes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_steps_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    upload: Mapped["Upload"] = relationship(back_populates="incidents")

    @property
    def severity_color(self) -> str:
        return {
            "low": "blue",
            "medium": "orange",
            "high": "red",
            "critical": "purple",
        }.get(self.severity, "gray")

    @property
    def possible_causes(self) -> list[str]:
        import json
        if self.possible_causes_json:
            return json.loads(self.possible_causes_json)
        return []

    @property
    def next_steps(self) -> list[str]:
        import json
        if self.next_steps_json:
            return json.loads(self.next_steps_json)
        return []


from app.models.upload import Upload  # noqa: E402
