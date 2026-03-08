"""Redact potential secrets from log messages before sending to LLM."""

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(password|passwd|pwd|secret|token|api_key|apikey)\s*[=:]\s*\S+"), r"\1=<REDACTED>"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer <REDACTED>"),
    (re.compile(r"Basic\s+[A-Za-z0-9+/]+=*"), "Basic <REDACTED>"),
]


def redact_secrets(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text
