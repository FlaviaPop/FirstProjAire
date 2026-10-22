"""Stdlib JSON-lines formatter for stdout logs (patterns §9; no third-party logging library)."""

import json
import logging
from datetime import UTC, datetime

from infrastructure.logging.sensitive import is_sensitive_log_key

REDACTED = "[redacted]"
_STANDARD = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}
_CONTEXT = ("request_id", "user_id", "role")
# Django attaches the HttpRequest to django.request/django.security records. Its repr carries
# the query string, which may hold personal data, so it is never serialised (patterns §9).
_NEVER_SERIALISED = frozenset({"request"})


class JsonFormatter(logging.Formatter):
    """One JSON object per line: fixed keys, request context, then the record's `extra` fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            **{key: getattr(record, key, None) for key in _CONTEXT},
        }
        payload.update(
            # Redact, never raise: logging must not fail a request (review v1 ISS-001).
            (key, REDACTED if is_sensitive_log_key(key) else value)
            for key, value in vars(record).items()
            if key not in _STANDARD and key not in _CONTEXT and key not in _NEVER_SERIALISED
        )
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)
