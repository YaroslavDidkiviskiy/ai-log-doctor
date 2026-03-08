from datetime import datetime

from app.models.log_event import LogEvent
from app.models.upload import Upload
from app.services.incident_grouper import group_events_into_incidents


def test_groups_by_fingerprint(db_session):
    upload = Upload(filename="test.log", stored_path="/tmp/test.log", status="processing")
    db_session.add(upload)
    db_session.flush()

    events = [
        LogEvent(
            upload_id=upload.id,
            message="Failed to validate token for user 183",
            normalized_message="failed to validate token for user <num>",
            fingerprint="aabb1122",
            level="ERROR",
            timestamp=datetime(2026, 3, 8, 12, 0, i),
        )
        for i in range(5)
    ]
    events.append(
        LogEvent(
            upload_id=upload.id,
            message="Connection refused to database",
            normalized_message="connection refused to database",
            fingerprint="ccdd3344",
            level="ERROR",
            timestamp=datetime(2026, 3, 8, 12, 1, 0),
        )
    )

    for e in events:
        db_session.add(e)
    db_session.flush()

    incidents = group_events_into_incidents(db_session, upload.id)
    assert len(incidents) == 2

    fp_counts = {i.fingerprint: i.count for i in incidents}
    assert fp_counts["aabb1122"] == 5
    assert fp_counts["ccdd3344"] == 1


def test_first_last_seen(db_session):
    upload = Upload(filename="test.log", stored_path="/tmp/test.log", status="processing")
    db_session.add(upload)
    db_session.flush()

    for i in range(3):
        db_session.add(
            LogEvent(
                upload_id=upload.id,
                message=f"Error #{i}",
                normalized_message="error <num>",
                fingerprint="same_fp",
                level="ERROR",
                timestamp=datetime(2026, 3, 8, 10 + i, 0, 0),
            )
        )
    db_session.flush()

    incidents = group_events_into_incidents(db_session, upload.id)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.first_seen == datetime(2026, 3, 8, 10, 0, 0)
    assert inc.last_seen == datetime(2026, 3, 8, 12, 0, 0)
