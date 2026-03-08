"""Parse log files into structured events.

Supported formats:
  - Plain:     2026-03-08 12:45:11 ERROR app.auth Failed to validate token
  - Bracketed: [2026-03-08 12:45:11] WARNING payments Timeout while calling provider
  - Python traceback blocks attached to the preceding error event
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

PLAIN_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
    r"\s+(?P<level>[A-Z]+)"
    r"\s+(?P<service>\S+)"
    r"\s+(?P<message>.+)$"
)

BRACKET_RE = re.compile(
    r"^\[(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)\]"
    r"\s+(?P<level>[A-Z]+)"
    r"\s+(?P<service>\S+)"
    r"\s+(?P<message>.+)$"
)

TRACEBACK_START_RE = re.compile(r"^Traceback \(most recent call last\):")
TRACEBACK_LINE_RE = re.compile(r"^\s+File |^\s+\w|^[A-Za-z]\w*(?:Error|Exception)")

IMPORTANT_PATTERNS = re.compile(
    r"(?i)(error|warning|exception|traceback|timeout|refused|failed|fatal|critical)"
)


@dataclass
class ParsedEvent:
    timestamp: datetime | None = None
    level: str | None = None
    service: str | None = None
    message: str = ""
    traceback: str | None = None
    line_number: int = 0


@dataclass
class ParseResult:
    events: list[ParsedEvent] = field(default_factory=list)
    total_lines: int = 0


def _parse_timestamp(ts_str: str) -> datetime | None:
    ts_str = ts_str.replace(",", ".")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def _match_log_line(line: str) -> ParsedEvent | None:
    for pattern in (BRACKET_RE, PLAIN_RE):
        m = pattern.match(line)
        if m:
            return ParsedEvent(
                timestamp=_parse_timestamp(m.group("ts")),
                level=m.group("level").upper(),
                service=m.group("service"),
                message=m.group("message").strip(),
            )
    return None


def _is_important(event: ParsedEvent) -> bool:
    if event.level and event.level in ("ERROR", "WARNING", "CRITICAL", "FATAL"):
        return True
    if IMPORTANT_PATTERNS.search(event.message):
        return True
    if event.traceback:
        return True
    return False


def parse_log_file(path: str | Path) -> ParseResult:
    path = Path(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    result = ParseResult(total_lines=len(lines))

    current_event: ParsedEvent | None = None
    in_traceback = False
    tb_lines: list[str] = []

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip()

        if TRACEBACK_START_RE.match(line):
            in_traceback = True
            tb_lines = [line]
            continue

        if in_traceback:
            if TRACEBACK_LINE_RE.match(line) or not line.strip():
                tb_lines.append(line)
                if re.match(r"^[A-Za-z]\w*(?:Error|Exception)", line):
                    in_traceback = False
                    tb_text = "\n".join(tb_lines)
                    if current_event:
                        current_event.traceback = tb_text
                    else:
                        current_event = ParsedEvent(
                            message=line.strip(),
                            traceback=tb_text,
                            line_number=line_num - len(tb_lines) + 1,
                            level="ERROR",
                        )
                    tb_lines = []
                continue
            else:
                in_traceback = False
                tb_text = "\n".join(tb_lines)
                if current_event:
                    current_event.traceback = tb_text
                tb_lines = []

        parsed = _match_log_line(line)
        if parsed:
            if current_event and _is_important(current_event):
                result.events.append(current_event)
            current_event = parsed
            current_event.line_number = line_num
        elif current_event and line.strip():
            current_event.message += " " + line.strip()

    if in_traceback and tb_lines:
        tb_text = "\n".join(tb_lines)
        if current_event:
            current_event.traceback = tb_text

    if current_event and _is_important(current_event):
        result.events.append(current_event)

    return result
