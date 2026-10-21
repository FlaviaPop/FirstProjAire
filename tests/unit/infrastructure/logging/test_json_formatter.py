import json
import logging
import sys
from datetime import datetime, timedelta

from infrastructure.logging.json_formatter import JsonFormatter
from infrastructure.logging.request_context import (
    RequestContextFilter,
    request_id_var,
    role_var,
    user_id_var,
)


def _record(msg: str = "probe", level: int = logging.INFO, **extra: object) -> logging.LogRecord:
    record = logging.LogRecord("qa.logger", level, __file__, 1, msg, None, None)
    record.__dict__.update(extra)
    return record


def _format(record: logging.LogRecord) -> dict[str, object]:
    RequestContextFilter().filter(record)
    return json.loads(JsonFormatter().format(record))


def test_line_has_the_fixed_keys_with_null_context_outside_a_request():
    payload = _format(_record("request.completed"))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "qa.logger"
    assert payload["event"] == "request.completed"
    assert (payload["request_id"], payload["user_id"], payload["role"]) == (None, None, None)


def test_timestamp_is_iso_8601_utc():
    payload = _format(_record())

    stamp = datetime.fromisoformat(str(payload["timestamp"]))
    assert stamp.utcoffset() == timedelta(0)


def test_request_context_variables_are_copied_onto_every_record():
    tokens = (request_id_var.set("abc12345"), user_id_var.set(7), role_var.set("TEACHER"))
    try:
        payload = _format(_record())
    finally:
        for var, token in zip((request_id_var, user_id_var, role_var), tokens, strict=True):
            var.reset(token)

    assert (payload["request_id"], payload["user_id"], payload["role"]) == (
        "abc12345",
        7,
        "TEACHER",
    )


def test_context_falls_back_to_the_attached_request_after_the_request_scope_ended():
    class _Request:
        log_context = ("late-1234", 7, "ADMIN")

    payload = _format(_record(request=_Request()))

    assert (payload["request_id"], payload["user_id"], payload["role"]) == ("late-1234", 7, "ADMIN")


def test_attached_object_without_log_context_leaves_context_null():
    payload = _format(_record(request=object()))

    assert (payload["request_id"], payload["user_id"], payload["role"]) == (None, None, None)


def test_context_variables_win_over_the_attached_request():
    class _Request:
        log_context = ("stale-1234", None, None)

    token = request_id_var.set("live-1234")
    try:
        payload = _format(_record(request=_Request()))
    finally:
        request_id_var.reset(token)

    assert payload["request_id"] == "live-1234"


def test_extra_fields_are_added_as_top_level_keys():
    payload = _format(_record(code="not_found", status=404))

    assert (payload["code"], payload["status"]) == ("not_found", 404)


def test_non_json_extras_are_stringified():
    payload = _format(_record(when=datetime(2026, 10, 21)))

    assert payload["when"] == "2026-10-21 00:00:00"


def test_attached_http_request_object_is_never_serialised():
    # Django attaches the HttpRequest; its repr contains the query string (PII risk).
    payload = _format(_record(request="<WSGIRequest: GET '/x?password=secret'>"))

    assert "request" not in payload
    assert "secret" not in json.dumps(payload)


def test_exception_info_is_included_as_text():
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = _record(level=logging.ERROR)
        record.exc_info = sys.exc_info()

    payload = _format(record)

    assert "RuntimeError: boom" in str(payload["exc_info"])


def test_non_ascii_text_is_kept_readable():
    line = JsonFormatter().format(_record("pagină"))

    assert "pagină" in line


def test_output_is_a_single_line():
    try:
        raise RuntimeError("multi\nline")
    except RuntimeError:
        record = _record(level=logging.ERROR)
        record.exc_info = sys.exc_info()
    RequestContextFilter().filter(record)

    assert "\n" not in JsonFormatter().format(record)
