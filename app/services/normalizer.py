"""Normalize log messages by replacing dynamic values with placeholders."""

import re

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_HEX_TOKEN_RE = re.compile(r"\b[0-9a-fA-F]{16,}\b")
_NUMBER_RE = re.compile(r"\b\d+\b")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_message(message: str) -> str:
    text = message
    text = _UUID_RE.sub("<uuid>", text)
    text = _IP_RE.sub("<ip>", text)
    text = _EMAIL_RE.sub("<email>", text)
    text = _HEX_TOKEN_RE.sub("<token>", text)
    text = _NUMBER_RE.sub("<num>", text)
    text = text.lower().strip()
    text = _WHITESPACE_RE.sub(" ", text)
    return text
