"""Story 1.0 review ISS-005: dev logs at DEBUG by default (patterns §10); other envs at INFO."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PRINT_LEVELS = (
    "import json; from django.conf import settings as s; print(json.dumps({"
    "'root': s.LOGGING['root']['level'], 'handler': s.LOGGING['handlers']['stdout']['level'],"
    "'django': s.LOGGING['loggers']['django']['level']}))"
)


def _levels(tmp_path: Path, settings_module: str, **env: str) -> dict[str, str]:
    base_env = {k: v for k, v in os.environ.items() if k != "LOG_LEVEL"}
    base_env |= {
        "DJANGO_SETTINGS_MODULE": settings_module,
        "DATABASE_PATH": str(tmp_path / "db.sqlite3"),
        **env,
    }
    result = subprocess.run(  # noqa: S603 — fixed interpreter and arguments, no user input
        [sys.executable, str(REPO_ROOT / "manage.py"), "shell", "--no-imports", "-c", PRINT_LEVELS],
        cwd=REPO_ROOT,
        env=base_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.slow
def test_dev_defaults_to_debug(tmp_path):
    assert _levels(tmp_path, "config.settings.dev") == {
        "root": "DEBUG",
        "handler": "DEBUG",
        "django": "INFO",  # stays INFO: django DEBUG would log SQL parameters (personal data)
    }


@pytest.mark.slow
def test_dev_level_can_be_overridden_by_environment(tmp_path):
    levels = _levels(tmp_path, "config.settings.dev", LOG_LEVEL="WARNING")

    assert (levels["root"], levels["handler"]) == ("WARNING", "WARNING")


@pytest.mark.slow
def test_prod_defaults_to_info(tmp_path):
    levels = _levels(
        tmp_path,
        "config.settings.prod",
        DJANGO_SECRET_KEY="x" * 50,
        DJANGO_ALLOWED_HOSTS="example.ro",
    )

    assert (levels["root"], levels["handler"], levels["django"]) == ("INFO", "INFO", "INFO")
