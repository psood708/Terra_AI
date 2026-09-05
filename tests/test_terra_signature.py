"""Unit tests for Terra webhook HMAC-SHA256 signature verification mechanics."""

from security.terra_signature import sign_terra_payload, verify_terra_signature

SECRET = "unit_test_signing_secret"


def test_valid_signature_verifies():
    body = b'{"event_id": "evt_1", "event_type": "daily"}'
    header = sign_terra_payload(body, SECRET, timestamp=1700000000)
    assert header.startswith("t=1700000000,v1=")
    assert verify_terra_signature(body, header, SECRET) is True


def test_wrong_secret_fails():
    body = b'{"event_id": "evt_1"}'
    header = sign_terra_payload(body, SECRET, timestamp=1700000000)
    assert verify_terra_signature(body, header, "a_different_secret") is False


def test_tampered_body_fails():
    body = b'{"event_id": "evt_1"}'
    header = sign_terra_payload(body, SECRET, timestamp=1700000000)
    tampered_body = b'{"event_id": "evt_2"}'
    assert verify_terra_signature(tampered_body, header, SECRET) is False


def test_downgrade_scheme_prefix_is_ignored():
    body = b'{"event_id": "evt_1"}'
    # A legacy/weaker "v0" scheme alongside a bogus v1 must not be trusted.
    forged_header = "t=1700000000,v0=anything,v1=deadbeef"
    assert verify_terra_signature(body, forged_header, SECRET) is False


def test_missing_signature_fails():
    assert verify_terra_signature(b"{}", "", SECRET) is False


def test_malformed_header_fails():
    assert verify_terra_signature(b"{}", "not-a-valid-header", SECRET) is False
