"""Group log events by fingerprint into incidents."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.log_event import LogEvent
from app.models.incident import Incident
from app.services.severity import detect_severity


def group_events_into_incidents(db: Session, upload_id: int) -> list[Incident]:
    events: list[LogEvent] = (
        db.query(LogEvent)
        .filter(LogEvent.upload_id == upload_id, LogEvent.fingerprint.isnot(None))
        .order_by(LogEvent.timestamp.asc().nullslast())
        .all()
    )

    groups: dict[str, list[LogEvent]] = {}
    for ev in events:
        groups.setdefault(ev.fingerprint, []).append(ev)

    incidents: list[Incident] = []
    for fp, group in groups.items():
        timestamps = [e.timestamp for e in group if e.timestamp]
        first_seen = min(timestamps) if timestamps else None
        last_seen = max(timestamps) if timestamps else None

        sample_event = group[0]
        sample_tb = next((e.traceback for e in group if e.traceback), None)
        primary_level = sample_event.level

        sev = detect_severity(
            normalized_message=sample_event.normalized_message or "",
            level=primary_level,
            count=len(group),
            has_traceback=sample_tb is not None,
        )

        incident = Incident(
            upload_id=upload_id,
            fingerprint=fp,
            title=_make_title(sample_event),
            severity=sev,
            count=len(group),
            first_seen=first_seen,
            last_seen=last_seen,
            sample_message=sample_event.message,
            sample_traceback=sample_tb,
        )
        db.add(incident)
        incidents.append(incident)

    db.flush()
    return incidents


def _make_title(event: LogEvent) -> str:
    msg = event.message or ""
    parts = []
    if event.level:
        parts.append(event.level)
    if event.service:
        parts.append(f"in {event.service}")
    snippet = msg[:80] + ("..." if len(msg) > 80 else "")
    parts.append(f"— {snippet}")
    return " ".join(parts)
