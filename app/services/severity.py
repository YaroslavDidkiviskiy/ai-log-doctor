"""Heuristic severity detection for incidents."""

import re

_CRITICAL_PATTERNS = re.compile(
    r"(?i)(fatal|database.*(down|unavailable)|out\s*of\s*memory|segfault|panic)"
)
_HIGH_PATTERNS = re.compile(
    r"(?i)(timeout|refused|connection.*(reset|closed)|traceback|crash|deadlock)"
)


def detect_severity(
    *,
    normalized_message: str,
    level: str | None,
    count: int,
    has_traceback: bool,
) -> str:
    if level and level.upper() in ("FATAL", "CRITICAL"):
        return "critical"
    if _CRITICAL_PATTERNS.search(normalized_message):
        return "critical"

    if _HIGH_PATTERNS.search(normalized_message):
        return "high"
    if has_traceback and count >= 3:
        return "high"

    if level and level.upper() == "ERROR":
        if count >= 5:
            return "high"
        return "medium"

    if level and level.upper() == "WARNING":
        if count >= 10:
            return "medium"
        return "low"

    return "medium"
