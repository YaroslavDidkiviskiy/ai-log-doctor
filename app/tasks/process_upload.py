"""Background task: full processing pipeline for an uploaded log file.

Pipeline steps:
  1. Parse log file into events
  2. Normalize messages & generate fingerprints
  3. Store LogEvent rows
  4. Group events into Incidents
  5. Detect severity
  6. AI summarize each incident
"""

import json
import logging
from datetime import datetime, timezone

from app.db import SessionLocal
from app.models.upload import Upload
from app.models.log_event import LogEvent
from app.services.log_parser import parse_log_file
from app.services.normalizer import normalize_message
from app.services.fingerprint import make_fingerprint
from app.services.incident_grouper import group_events_into_incidents
from app.services.summarizer import get_summarizer
from app.services.secret_redactor import redact_secrets

logger = logging.getLogger(__name__)


def process_upload(upload_id: int) -> None:
    db = SessionLocal()
    try:
        upload = db.get(Upload, upload_id)
        if not upload:
            logger.error("Upload %s not found", upload_id)
            return

        upload.status = "processing"
        db.commit()

        result = parse_log_file(upload.stored_path)
        upload.total_lines = result.total_lines

        events: list[LogEvent] = []
        for parsed in result.events:
            normalized = normalize_message(parsed.message)
            fp = make_fingerprint(normalized)

            event = LogEvent(
                upload_id=upload_id,
                timestamp=parsed.timestamp,
                level=parsed.level,
                service=parsed.service,
                message=parsed.message,
                normalized_message=normalized,
                fingerprint=fp,
                traceback=parsed.traceback,
                line_number=parsed.line_number,
            )
            db.add(event)
            events.append(event)

        db.flush()
        upload.total_events = len(events)

        incidents = group_events_into_incidents(db, upload_id)
        upload.total_incidents = len(incidents)

        summarizer = get_summarizer()
        for incident in incidents:
            try:
                related_events = [
                    e for e in events if e.fingerprint == incident.fingerprint
                ]
                sample_msgs = [redact_secrets(e.message) for e in related_events[:3]]
                tb = incident.sample_traceback
                if tb:
                    tb = redact_secrets(tb)

                summary = summarizer.summarize(
                    normalized_message=incident.sample_message or "",
                    sample_messages=sample_msgs,
                    sample_traceback=tb,
                    count=incident.count,
                    service=related_events[0].service if related_events else None,
                    first_seen=incident.first_seen.isoformat() if incident.first_seen else None,
                    last_seen=incident.last_seen.isoformat() if incident.last_seen else None,
                )

                incident.title = summary.title
                incident.ai_summary = summary.summary
                incident.possible_causes_json = json.dumps(summary.possible_causes)
                incident.next_steps_json = json.dumps(summary.next_steps)
                if summary.severity:
                    incident.severity = summary.severity

            except Exception:
                logger.exception(
                    "Failed to summarize incident %s", incident.fingerprint
                )

        upload.status = "done"
        upload.processed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Upload %s processed: %d lines, %d events, %d incidents",
            upload_id,
            upload.total_lines,
            upload.total_events,
            upload.total_incidents,
        )

    except Exception as exc:
        logger.exception("Failed to process upload %s", upload_id)
        try:
            upload = db.get(Upload, upload_id)
            if upload:
                upload.status = "failed"
                upload.error_message = str(exc)[:500]
                db.commit()
        except Exception:
            logger.exception("Failed to update upload status")
    finally:
        db.close()
