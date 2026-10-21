import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.urls import path

from domain.common.errors import NotFound
from infrastructure.web.common.health import healthz
from tests.factories.accounts import UserFactory

# capfd (not capsys): the logging handler holds the real stdout captured at settings load time.
REPO_ROOT = Path(__file__).resolve().parents[4]


def _raise(exc):
    def view(request):
        raise exc

    return view


urlpatterns = [
    path("healthz", healthz),
    path("nf", _raise(NotFound())),
    path("boom", _raise(RuntimeError("secret internal detail"))),
]
handler404 = "infrastructure.web.common.errors.handle_404"
handler500 = "infrastructure.web.common.errors.handle_500"

pytestmark = [pytest.mark.django_db, pytest.mark.urls(__name__)]


def _json_lines(capfd):
    return [
        json.loads(line) for line in capfd.readouterr().out.splitlines() if line.startswith("{")
    ]


def _completed_lines(capfd):
    return [line for line in _json_lines(capfd) if line["event"] == "request.completed"]


def test_response_header_matches_logged_request_id(client, capfd):
    response = client.get("/healthz")

    (line,) = _completed_lines(capfd)
    assert response["X-Request-ID"] == line["request_id"]
    assert (line["status"], line["path"], line["user_id"]) == (200, "/healthz", None)


def test_request_completed_line_has_method_status_and_duration(client, capfd):
    client.get("/healthz")

    (line,) = _completed_lines(capfd)
    assert line["level"] == "INFO"
    assert line["method"] == "GET"
    assert isinstance(line["duration_ms"], int | float)
    assert line["duration_ms"] >= 0
    assert line["role"] is None


def test_generated_request_id_is_32_hex_characters(client):
    request_id = client.get("/healthz")["X-Request-ID"]

    assert len(request_id) == 32
    int(request_id, 16)


def test_valid_incoming_request_id_is_reused(client):
    assert client.get("/healthz", headers={"X-Request-ID": "proxy-1234"})["X-Request-ID"] == (
        "proxy-1234"
    )


def test_valid_incoming_request_id_appears_in_log_lines(client, capfd):
    client.get("/healthz", headers={"X-Request-ID": "abc12345-proxy"})

    (line,) = _completed_lines(capfd)
    assert line["request_id"] == "abc12345-proxy"


@pytest.mark.parametrize("good", ["a" * 8, "A1-b2-C3", "z" * 64])
def test_boundary_valid_incoming_ids_are_reused(client, good):
    assert client.get("/healthz", headers={"X-Request-ID": good})["X-Request-ID"] == good


@pytest.mark.parametrize("bad", ["<script>", "x" * 65, "short", "a b c d e f g h", "", "abc_1234"])
def test_invalid_incoming_request_id_is_replaced(client, capfd, bad):
    returned = client.get("/healthz", headers={"X-Request-ID": bad})["X-Request-ID"]

    assert returned != bad
    assert len(returned) == 32
    if bad:
        assert bad not in capfd.readouterr().out


def test_each_request_logs_exactly_one_completed_line(client, capfd):
    client.get("/healthz")
    client.get("/nf")

    lines = _completed_lines(capfd)
    assert [line["status"] for line in lines] == [200, 404]
    assert lines[0]["request_id"] != lines[1]["request_id"]


def test_query_string_values_never_reach_logs(client, capfd):
    client.get("/healthz?password=secret&dob=2018-01-01")

    output = capfd.readouterr().out
    assert "secret" not in output
    assert "2018-01-01" not in output


def test_query_string_never_reaches_logs_on_errors(client, capfd):
    client.raise_request_exception = False
    client.get("/boom?password=secret")
    client.get("/missing?password=secret")

    output = capfd.readouterr().out
    assert "password=secret" not in output


def test_no_personal_data_of_a_signed_in_user_reaches_logs(client, capfd):
    user = UserFactory(full_name="Ana Popescu", role="TEACHER")
    client.force_login(user)

    client.get("/healthz")

    output = capfd.readouterr().out
    assert "Ana Popescu" not in output
    assert "2018-05-01" not in output
    assert user.password not in output


def test_signed_in_user_id_and_role_are_attached(client, capfd):
    user = UserFactory(role="TEACHER")
    client.force_login(user)

    client.get("/healthz")

    (line,) = _completed_lines(capfd)
    assert (line["user_id"], line["role"]) == (user.pk, "TEACHER")


def test_context_does_not_leak_into_the_next_request(client, capfd):
    client.force_login(UserFactory(role="TEACHER"))
    client.get("/healthz")
    client.logout()

    client.get("/healthz")

    assert _completed_lines(capfd)[-1]["user_id"] is None


def test_domain_error_logs_one_info_line_with_code_and_status(client, capfd):
    response = client.get("/nf")

    (line,) = [line for line in _json_lines(capfd) if line["event"] == "domain_error"]
    assert (line["level"], line["code"], line["status"]) == ("INFO", "not_found", 404)
    assert line["request_id"] == response["X-Request-ID"]


def test_unexpected_error_logs_error_with_exc_info_and_same_request_id(client, capfd):
    client.raise_request_exception = False

    response = client.get("/boom")

    lines = _json_lines(capfd)
    (error,) = [line for line in lines if line["level"] == "ERROR"]
    assert error["logger"] == "django.request"
    assert "RuntimeError: secret internal detail" in error["exc_info"]
    assert error["request_id"] == response["X-Request-ID"]
    assert f"Reference: {response['X-Request-ID']}" in response.content.decode()
    (completed,) = [line for line in lines if line["event"] == "request.completed"]
    assert (completed["status"], completed["request_id"]) == (500, response["X-Request-ID"])


@pytest.mark.parametrize("url", ["/nf", "/missing", "/boom"])
def test_every_line_of_a_failing_request_carries_its_request_id(client, capfd, url):
    # Django logs 4xx/5xx warnings after the middleware chain has returned.
    client.raise_request_exception = False

    response = client.get(url)

    lines = _json_lines(capfd)
    assert any(line["logger"] == "django.request" for line in lines)
    assert {line["request_id"] for line in lines} == {response["X-Request-ID"]}


def test_late_django_lines_carry_the_signed_in_user(client, capfd):
    user = UserFactory(role="TEACHER")
    client.force_login(user)

    client.get("/nf")

    (warning,) = [line for line in _json_lines(capfd) if line["logger"] == "django.request"]
    assert (warning["user_id"], warning["role"]) == (user.pk, "TEACHER")


def test_log_lines_are_json_with_context_keys(capfd):
    logging.getLogger("qa").info("probe", extra={"code": "x"})

    record = json.loads(capfd.readouterr().out.strip().splitlines()[-1])
    assert {"timestamp", "level", "logger", "event", "request_id", "user_id", "role", "code"} <= (
        record.keys()
    )


def test_every_stdout_line_is_json(client, capfd):
    client.raise_request_exception = False
    client.get("/healthz")
    client.get("/nf")
    client.get("/boom")

    for line in capfd.readouterr().out.splitlines():
        json.loads(line)


def _root_level(log_level: str | None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "LOG_LEVEL"}
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
    if log_level is not None:
        env["LOG_LEVEL"] = log_level
    result = subprocess.run(  # noqa: S603 — fixed interpreter and arguments, no user input
        [
            sys.executable,
            str(REPO_ROOT / "manage.py"),
            "shell",
            "--no-imports",
            "-c",
            "import logging; print(logging.getLevelName(logging.getLogger().level))",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip().splitlines()[-1]


@pytest.mark.slow
@pytest.mark.parametrize(("log_level", "expected"), [(None, "INFO"), ("WARNING", "WARNING")])
def test_root_log_level_comes_from_log_level_env(log_level, expected):
    assert _root_level(log_level) == expected
