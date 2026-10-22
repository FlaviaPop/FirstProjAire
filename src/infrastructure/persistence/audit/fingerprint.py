"""Keyed fingerprint for typed usernames that don't belong to an account (review v1 ISS-003).

HMAC-SHA256 with SECRET_KEY, truncated to 8 hex characters: enough to correlate repeated
attempts with the same text in the audit log, without storing (or allowing a dictionary
lookup of) what was typed, which may be a mistyped password.
"""

import hashlib
import hmac

from django.conf import settings

FINGERPRINT_LENGTH = 8


def username_fingerprint(value: str) -> str:
    """Implements `application.accounts.record_security_event.Fingerprint`."""
    digest = hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()
    return digest[:FINGERPRINT_LENGTH]
