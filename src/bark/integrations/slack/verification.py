"""Slack request signature verification."""

import hashlib
import hmac
import time

from fastapi import Request, HTTPException


def verify_slack_signature_from_body(
    body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str,
) -> None:
    """Verify that a request came from Slack.

    Args:
        body: The request body bytes
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
        signing_secret: The Slack signing secret

    Raises:
        HTTPException: If verification fails
    """
    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="Missing Slack headers")

    # Check timestamp to prevent replay attacks (5 minutes tolerance)
    try:
        request_time = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    current_time = int(time.time())
    if abs(current_time - request_time) > 300:
        raise HTTPException(status_code=401, detail="Request too old")

    # Compute expected signature
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    expected_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
    )

    # Compare signatures
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
