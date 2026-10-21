"""`manage.py migrate` behaviour of the catalogue app on a fresh file DB (separate processes).

Mirrors what an installation, a restart and a rollback do: each step is its own process
against the same SQLite file.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]

ACTIVE_SUBJECTS = (
    "from infrastructure.persistence.catalogue.models import SubjectModel as S;"
    "print(sorted(S.objects.filter(is_active=True).values_list('grade__code', 'code')))"
)
COUNTS = (
    "from infrastructure.persistence.catalogue.models import GradeModel as G, SubjectModel as S;"
    "print(G.objects.count(), S.objects.count())"
)
CATALOGUE_TABLES = (
    "from django.db import connection;"
    "print(sorted(t for t in connection.introspection.table_names() if t.startswith('catalogue')))"
)


def _manage(db_path: Path, *args: str) -> str:
    env = os.environ | {
        "DJANGO_SETTINGS_MODULE": "config.settings.dev",
        "DATABASE_PATH": str(db_path),
    }
    result = subprocess.run(  # noqa: S603 — fixed interpreter and arguments, no user input
        [sys.executable, str(REPO_ROOT / "manage.py"), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _shell(db_path: Path, code: str) -> str:
    return _manage(db_path, "shell", "--no-imports", "-c", code)


@pytest.mark.slow
def test_migrate_on_empty_db_applies_schema_then_seed(tmp_path):
    db_path = tmp_path / "db.sqlite3"

    output = _manage(db_path, "migrate", "--noinput")

    assert "Applying catalogue.0001_initial... OK" in output
    assert "Applying catalogue.0002_seed_catalogue... OK" in output
    assert output.index("catalogue.0001_initial") < output.index("catalogue.0002_seed_catalogue")
    assert _shell(db_path, COUNTS) == "9 106"


@pytest.mark.slow
def test_seeded_catalogue_survives_restart_and_repeat_migrate(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    _manage(db_path, "migrate", "--noinput", "-v", "0")

    repeat = _manage(db_path, "migrate", "--noinput")

    assert "No migrations to apply." in repeat
    assert _shell(db_path, ACTIVE_SUBJECTS) == "[('2', 'CLR'), ('2', 'EN'), ('2', 'MEM')]"


@pytest.mark.slow
def test_migrate_catalogue_zero_then_migrate_round_trips(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    _manage(db_path, "migrate", "--noinput", "-v", "0")

    reverse = _manage(db_path, "migrate", "catalogue", "zero", "--noinput")
    tables_after_reverse = _shell(db_path, CATALOGUE_TABLES)
    _manage(db_path, "migrate", "--noinput", "-v", "0")

    assert reverse.index("Unapplying catalogue.0002_seed_catalogue... OK") < reverse.index(
        "Unapplying catalogue.0001_initial... OK"
    )
    assert tables_after_reverse == "[]"
    assert _shell(db_path, COUNTS) == "9 106"


@pytest.mark.slow
def test_reverse_of_seed_only_keeps_the_schema_and_removes_the_rows(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    _manage(db_path, "migrate", "--noinput", "-v", "0")

    _manage(db_path, "migrate", "catalogue", "0001", "--noinput", "-v", "0")

    assert _shell(db_path, COUNTS) == "0 0"
    assert _shell(db_path, CATALOGUE_TABLES) == "['catalogue_grade', 'catalogue_subject']"
