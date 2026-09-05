"""
Terra webhook HMAC-SHA256 signature verification.

Terra signs webhook deliveries with a `terra-signature: t=<unix_ts>,v1=<hex_hmac>`
header. The HMAC is computed over `"{timestamp}.{raw_body}"` using the
account's signing secret, matching the scheme documented at
https://docs.tryterra.co/docs/webhooks and implemented in Terra's own
`terra` PyPI package's `verify_terra_signature` helper.
"""

import hashlib
import hmac
import time
from typing import Optional


def _digest(raw_body: bytes, timestamp: str, signing_secret: str) -> str:
    message = f"{timestamp}.".encode("utf-8") + raw_body
    return hmac.new(signing_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def sign_terra_payload(raw_body: bytes, signing_secret: str, timestamp: Optional[int] = None) -> str:
    """Build a `terra-signature` header value the same way Terra does.

    Used by tests to produce a realistic signed request without a live Terra account.
    """
    ts = str(timestamp if timestamp is not None else int(time.time()))
    return f"t={ts},v1={_digest(raw_body, ts, signing_secret)}"


def verify_terra_signature(raw_body: bytes, signature_header: str, signing_secret: str) -> bool:
    """Verify a `terra-signature` header against the raw (unparsed) request body.

    Only the `v1` scheme is trusted — other prefixes are ignored so a
    downgrade to a weaker/legacy scheme can't be used to bypass verification.
    Comparison is constant-time to avoid leaking the expected digest via timing.
    """
    if not signature_header:
        return False

    parts: dict[str, str] = {}
    for chunk in signature_header.split(","):
        key, sep, value = chunk.strip().partition("=")
        if sep:
            parts[key] = value

    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False

    expected = _digest(raw_body, timestamp, signing_secret)
    return hmac.compare_digest(expected, signature)
