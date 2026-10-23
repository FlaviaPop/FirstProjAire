"""Prod switches read from the environment (review hand-offs to DevOps, remediated 2026-10-23).

- Story 1.1 review v1 ISS-004: the incoming `X-Request-ID` is trusted only behind the proxy.
- BUG-004: axes reads X-Forwarded-For (overwritten by Nginx) only in prod, proxy count 0.
- Story 1.0 review v1 ISS-004: HSTS `includeSubDomains`/`preload` stay off until the domain is
  final (owner decision); while off, Django's W005/W021 deploy warnings are silenced on purpose.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PRINT_SETTINGS = (
    "import json; from django.conf import settings as s; print(json.dumps({"
    "'trust_request_id': s.TRUST_INCOMING_REQUEST_ID,"
    "'hsts_subdomains': s.SECURE_HSTS_INCLUDE_SUBDOMAINS, 'hsts_preload': s.SECURE_HSTS_PRELOAD,"
    "'silenced': s.SILENCED_SYSTEM_CHECKS,"
    "'ip_headers': list(s.AXES_IPWARE_META_PRECEDENCE_ORDER),"
    "'proxy_count': s.AXES_IPWARE_PROXY_COUNT}))"
)
SWITCHES = (
    "DJANGO_TRUST_INCOMING_REQUEST_ID",
    "DJANGO_HSTS_INCLUDE_SUBDOMAINS",
    "DJANGO_HSTS_PRELOAD",
    "DJANGO_TRUST_X_FORWARDED_FOR",
    "AXES_PROXY_COUNT",
)


def _env(tmp_path: Path, settings_module: str, **env: str) -> dict[str, str]:
    base_env = {k: v for k, v in os.environ.items() if k not in SWITCHES}
    return base_env | {
        "DJANGO_SETTINGS_MODULE": settings_module,
        "DATABASE_PATH": str(tmp_path / "db.sqlite3"),
        "DJANGO_SECRET_KEY": "x" * 50,
        "DJANGO_ALLOWED_HOSTS": "example.ro",
        **env,
    }


def _manage(tmp_path: Path, settings_module: str, *args: str, **env: str):
    return subprocess.run(  # noqa: S603 — fixed interpreter and arguments, no user input
        [sys.executable, str(REPO_ROOT / "manage.py"), *args],
        cwd=REPO_ROOT,
        env=_env(tmp_path, settings_module, **env),
        capture_output=True,
        text=True,
        check=False,
    )


def _settings(tmp_path: Path, settings_module: str = "config.settings.prod", **env: str) -> dict:
    result = _manage(
        tmp_path, settings_module, "shell", "--no-imports", "-c", PRINT_SETTINGS, **env
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.slow
def test_prod_trusts_the_proxy_request_id_by_default(tmp_path):
    assert _settings(tmp_path)["trust_request_id"] is True


@pytest.mark.slow
def test_prod_request_id_trust_can_be_switched_off(tmp_path):
    settings = _settings(tmp_path, DJANGO_TRUST_INCOMING_REQUEST_ID="false")

    assert settings["trust_request_id"] is False


@pytest.mark.slow
def test_dev_never_trusts_a_client_request_id(tmp_path):
    settings = _settings(tmp_path, "config.settings.dev", DJANGO_TRUST_INCOMING_REQUEST_ID="true")

    assert settings["trust_request_id"] is False


@pytest.mark.slow
def test_prod_hsts_flags_default_off_and_their_warnings_are_silenced(tmp_path):
    settings = _settings(tmp_path)

    assert (settings["hsts_subdomains"], settings["hsts_preload"]) == (False, False)
    assert {"security.W005", "security.W021"} <= set(settings["silenced"])


@pytest.mark.slow
def test_prod_hsts_flags_switched_on_are_not_silenced(tmp_path):
    settings = _settings(
        tmp_path, DJANGO_HSTS_INCLUDE_SUBDOMAINS="true", DJANGO_HSTS_PRELOAD="true"
    )

    assert (settings["hsts_subdomains"], settings["hsts_preload"]) == (True, True)
    assert not {"security.W005", "security.W021"} & set(settings["silenced"])


@pytest.mark.slow
def test_prod_silences_only_the_flag_that_is_off(tmp_path):
    settings = _settings(tmp_path, DJANGO_HSTS_INCLUDE_SUBDOMAINS="true")

    assert "security.W005" not in settings["silenced"]
    assert "security.W021" in settings["silenced"]


@pytest.mark.slow
def test_prod_deploy_check_has_no_hsts_warnings(tmp_path):
    result = _manage(tmp_path, "config.settings.prod", "check", "--deploy")

    assert result.returncode == 0, result.stderr
    assert "W005" not in result.stderr + result.stdout
    assert "W021" not in result.stderr + result.stdout


@pytest.mark.slow
def test_prod_rejects_an_unreadable_switch(tmp_path):
    result = _manage(tmp_path, "config.settings.prod", "check", DJANGO_HSTS_PRELOAD="yes-please")

    assert result.returncode != 0
    assert "DJANGO_HSTS_PRELOAD" in result.stderr


@pytest.mark.slow
def test_prod_reads_the_client_ip_from_the_proxy_header_by_default(tmp_path):
    settings = _settings(tmp_path)

    assert settings["ip_headers"] == ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]
    assert settings["proxy_count"] == 0


@pytest.mark.slow
def test_prod_proxy_header_trust_can_be_switched_off(tmp_path):
    settings = _settings(tmp_path, DJANGO_TRUST_X_FORWARDED_FOR="false")

    assert settings["ip_headers"] == ["REMOTE_ADDR"]


@pytest.mark.slow
def test_dev_never_reads_the_forwarded_for_header(tmp_path):
    settings = _settings(tmp_path, "config.settings.dev", DJANGO_TRUST_X_FORWARDED_FOR="true")

    assert settings["ip_headers"] == ["REMOTE_ADDR"]
