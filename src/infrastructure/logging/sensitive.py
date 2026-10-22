"""One rule for "sensitive" field names, shared by the JSON logs and the audit log (patterns §9).

Keys are case-folded and `-` is treated as `_`, so `Password`, `new_password`, `Date-Of-Birth`
and `refresh_token` all match. Story 1.8 review v1 ISS-001 (audit) and Story 1.1 review v1
ISS-001 (logs).
"""

# A key *containing* any of these is sensitive: credentials, dates of birth, test answers.
SENSITIVE_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "birth",
    "dob",
    "answer",
    "response",
)
# Exact keys that are personal data in logs. Not fragments: "reason" alone (e.g. Django's
# CSRF failure reason) is operational detail, but moderation block reasons are not.
PERSONAL_LOG_KEYS = frozenset(
    {"full_name", "first_name", "last_name", "body", "block_reason", "moderation_reason"}
)


def _normalise(key: str) -> str:
    return key.casefold().replace("-", "_")


def is_sensitive_key(key: str) -> bool:
    """True if `key` names a password, secret, token, date of birth or test answer."""
    normalised = _normalise(key)
    return any(fragment in normalised for fragment in SENSITIVE_FRAGMENTS)


def is_sensitive_log_key(key: str) -> bool:
    """`is_sensitive_key`, plus personal-data keys that must never reach operational logs."""
    return is_sensitive_key(key) or _normalise(key) in PERSONAL_LOG_KEYS
