"""Story 1.1 review v1 ISS-001: the JSON formatter never writes sensitive `extra` fields."""

import json
import logging

import pytest

from infrastructure.logging.json_formatter import REDACTED, JsonFormatter


def _format(**extra):
    record = logging.makeLogRecord(
        {"name": "x", "msg": "account.updated", "levelno": 20, "levelname": "INFO", **extra}
    )
    return json.loads(JsonFormatter().format(record))


@pytest.mark.parametrize(
    "key",
    [
        "password", "Password", "new_password", "token", "csrf_token", "client_secret",
        "date_of_birth", "dob", "birthdate", "answer", "answers", "test_responses",
        "full_name", "first_name", "last_name", "body", "block_reason", "moderation_reason",
    ],
)  # fmt: skip
def test_sensitive_extra_fields_are_redacted(key):
    line = _format(**{key: "Ana Pop 2018-01-01 hunter2"})

    assert line[key] == REDACTED
    assert "hunter2" not in json.dumps(line)


@pytest.mark.parametrize(
    ("key", "value"),
    [("count", 3), ("status", 404), ("code", "not_found"), ("reason", "CSRF cookie not set."),
     ("audit_action", "auth.login"), ("duration_ms", 1.5), ("path", "/ro/")],
)  # fmt: skip
def test_ordinary_extra_fields_are_kept(key, value):
    assert _format(**{key: value})[key] == value


def test_fixed_keys_are_never_redacted():
    line = _format(password="x")

    assert (line["event"], line["level"], line["logger"]) == ("account.updated", "INFO", "x")
