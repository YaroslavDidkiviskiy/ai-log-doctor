import tempfile
import os

from app.services.log_parser import parse_log_file


def test_parse_plain_log_lines(sample_log_file):
    result = parse_log_file(sample_log_file)
    assert result.total_lines > 0
    assert len(result.events) > 0

    levels = {e.level for e in result.events}
    assert "ERROR" in levels


def test_parse_bracketed_format():
    content = """\
[2026-03-08 09:00:01] INFO uvicorn Application startup
[2026-03-08 09:00:05] ERROR app.api Failed to connect to database
[2026-03-08 09:00:08] WARNING app.cache Cache miss rate above 80%
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        result = parse_log_file(path)
        assert result.total_lines == 3
        errors = [e for e in result.events if e.level == "ERROR"]
        assert len(errors) == 1
        assert "database" in errors[0].message
    finally:
        os.unlink(path)


def test_parse_traceback_attachment(sample_log_file):
    result = parse_log_file(sample_log_file)
    events_with_tb = [e for e in result.events if e.traceback]
    assert len(events_with_tb) >= 1
    assert "TimeoutError" in events_with_tb[0].traceback


def test_filters_only_important_events():
    content = """\
2026-03-08 12:00:01 INFO app.server Application started
2026-03-08 12:00:02 DEBUG app.db Query executed in 5ms
2026-03-08 12:00:03 INFO app.server Request handled
2026-03-08 12:00:04 INFO app.server Health check OK
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name

    try:
        result = parse_log_file(path)
        assert len(result.events) == 0, "Should not capture INFO/DEBUG-only logs"
    finally:
        os.unlink(path)
