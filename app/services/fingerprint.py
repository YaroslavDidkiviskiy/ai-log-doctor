"""Generate stable fingerprints from normalized messages."""

import hashlib


def make_fingerprint(normalized_message: str) -> str:
    return hashlib.sha256(normalized_message.encode("utf-8")).hexdigest()[:16]
