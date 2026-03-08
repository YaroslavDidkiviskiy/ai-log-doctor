from app.services.normalizer import normalize_message


def test_replaces_uuid():
    msg = "Failed for user a3f8e2b1-4c5d-4e6f-8a9b-1c2d3e4f5a6b"
    result = normalize_message(msg)
    assert "<uuid>" in result
    assert "a3f8e2b1" not in result


def test_replaces_ip():
    msg = "Connection from 192.168.1.14 refused"
    result = normalize_message(msg)
    assert "<ip>" in result
    assert "192.168.1.14" not in result


def test_replaces_email():
    msg = "Failed to send to user@example.com"
    result = normalize_message(msg)
    assert "<email>" in result
    assert "user@example.com" not in result


def test_replaces_numbers():
    msg = "User 183 failed to authenticate"
    result = normalize_message(msg)
    assert "<num>" in result
    assert "183" not in result


def test_replaces_hex_tokens():
    msg = "Invalid token abc123def456abc123def456abc123de"
    result = normalize_message(msg)
    assert "<token>" in result


def test_lowercases_and_normalizes_whitespace():
    msg = "User   Failed   to   AUTHENTICATE"
    result = normalize_message(msg)
    assert result == "user failed to authenticate"


def test_combined_normalization():
    msg = "User 183 failed to authenticate from IP 192.168.1.14"
    result = normalize_message(msg)
    assert result == "user <num> failed to authenticate from ip <ip>"
