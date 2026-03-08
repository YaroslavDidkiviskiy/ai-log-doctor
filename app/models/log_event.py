from datetime import datetime, timezone

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class LogEvent(Base):
    __tablename__ = "log_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    upload_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("uploads.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    service: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    upload: Mapped["Upload"] = relationship(back_populates="log_events")


from app.models.upload import Upload  # noqa: E402
