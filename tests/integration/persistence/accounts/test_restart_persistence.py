"""Data must survive a process restart (ADR-004: file-based SQLite on a persistent volume).

Each step runs in its own Python process against the same database file, which is what a
server stop/start does. The prod-settings start-up checks use the same subprocess helper.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

CREATE_USER = (
    "from django.contrib.auth import get_user_model as g;"
    "g().objects.create_user(username='kept', password='pilot-pass-123',"
    " full_name='Kept User', date_of_birth='2018-01-01', role='STUDENT')"
)
COUNT_USERS = "from django.contrib.auth import get_user_model as g; print(g().objects.count())"


def _run_manage(env_overrides: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"} | env_overrides
    return subprocess.run(  # noqa: S603 — fixed interpreter and arguments, no user input
        [sys.executable, str(REPO_ROOT / "manage.py"), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _manage_dev(db_path: Path, *args: str) -> str:
    result = _run_manage(
        {"DJANGO_SETTINGS_MODULE": "config.settings.dev", "DATABASE_PATH": str(db_path)}, *args
    )
    # Surface Django's traceback in the failure message instead of a bare exit code.
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _prod_check(tmp_path: Path, **env_overrides: str) -> subprocess.CompletedProcess[str]:
    env = {"DJANGO_SETTINGS_MODULE": "config.settings.prod", "DATABASE_PATH": str(tmp_path / "db")}
    return _run_manage(env | env_overrides, "check")


@pytest.mark.slow
def test_users_survive_a_process_restart(tmp_path):
    db_path = tmp_path / "data" / "db.sqlite3"

    _manage_dev(db_path, "migrate", "--noinput", "-v", "0")
    _manage_dev(db_path, "shell", "--no-imports", "-c", CREATE_USER)
    count_after_restart = _manage_dev(db_path, "shell", "--no-imports", "-c", COUNT_USERS)

    assert count_after_restart == "1"
    assert db_path.exists()


@pytest.mark.slow
def test_migrate_twice_reports_nothing_to_apply(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    _manage_dev(db_path, "migrate", "--noinput", "-v", "0")

    assert "No migrations to apply." in _manage_dev(db_path, "migrate", "--noinput")


@pytest.mark.slow
def test_prod_settings_refuse_to_start_without_secret_key(tmp_path):
    result = _prod_check(tmp_path, DJANGO_ALLOWED_HOSTS="example.ro")

    assert result.returncode != 0
    assert "Required environment variable DJANGO_SECRET_KEY is not set" in result.stderr


@pytest.mark.slow
def test_prod_settings_refuse_to_start_with_empty_allowed_hosts(tmp_path):
    result = _prod_check(tmp_path, DJANGO_SECRET_KEY="x" * 50, DJANGO_ALLOWED_HOSTS=" , ")

    assert result.returncode != 0
    assert "DJANGO_ALLOWED_HOSTS must list at least one host" in result.stderr


@pytest.mark.slow
def test_prod_settings_start_with_secret_key_and_hosts(tmp_path):
    result = _prod_check(tmp_path, DJANGO_SECRET_KEY="x" * 50, DJANGO_ALLOWED_HOSTS="example.ro")

    assert result.returncode == 0, result.stderr
