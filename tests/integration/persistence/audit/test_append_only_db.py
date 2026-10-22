"""Review v1 ISS-002: audit_log is append-only in the database itself (SQLite triggers), not
only through `AuditLogModel.objects`. Raw SQL, `_base_manager` and dbshell are covered too."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from django.db import DatabaseError, connection, transaction

from infrastructure.persistence.audit.models import AuditLogModel
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from tests.factories.accounts import UserFactory
from tests.fakes import FixedClock

pytestmark = pytest.mark.django_db
REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def row():
    user = UserFactory(username="ana")
    DjangoAuditPort(FixedClock()).record("auth.login", actor_id=user.pk, actor_username="ana")
    return AuditLogModel.objects.get()


def _sql(statement, params=()):
    with connection.cursor() as cursor:
        cursor.execute(statement, params)


def test_raw_sql_update_is_rejected(row):
    with pytest.raises(DatabaseError, match="append-only"):
        _sql("UPDATE audit_log SET action = 'tampered' WHERE id = %s", [row.pk])

    assert AuditLogModel.objects.get().action == "auth.login"


def test_raw_sql_delete_is_rejected(row):
    with pytest.raises(DatabaseError, match="append-only"):
        _sql("DELETE FROM audit_log WHERE id = %s", [row.pk])

    assert AuditLogModel.objects.count() == 1


def test_base_manager_update_is_rejected(row):
    # QuerySet.update() marks the enclosing transaction for rollback on error: use a savepoint.
    with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
        AuditLogModel._base_manager.filter(pk=row.pk).update(actor_username="mallory")

    assert AuditLogModel.objects.get().actor_username == "ana"


@pytest.mark.parametrize(
    ("column", "value"),
    [("actor_username", "mallory"), ("metadata", '{"x": 1}'), ("ip_address", "10.0.0.9")],
)
def test_unlinking_the_actor_cannot_smuggle_other_changes(row, column, value):
    with pytest.raises(DatabaseError, match="append-only"):
        _sql(f"UPDATE audit_log SET actor_id = NULL, {column} = %s WHERE id = %s", [value, row.pk])  # noqa: S608 — column from a fixed test list


def test_unlinking_the_actor_alone_is_allowed(row):
    _sql("UPDATE audit_log SET actor_id = NULL WHERE id = %s", [row.pk])

    assert AuditLogModel.objects.get().actor_id is None


def test_account_deletion_still_unlinks_and_keeps_the_row(row):
    row_user = row.actor_id

    UserFactory._meta.model.objects.get(pk=row_user).delete()

    kept = AuditLogModel.objects.get()
    assert (kept.actor_id, kept.actor_username) == (None, "ana")


@pytest.mark.slow
def test_trigger_migration_is_reversible(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.dev",
        "DATABASE_PATH": str(db_path),
    }

    def manage(*args):
        result = subprocess.run(  # noqa: S603 — fixed interpreter and arguments
            [sys.executable, str(REPO_ROOT / "manage.py"), *args],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, check=False,
        )  # fmt: skip
        assert result.returncode == 0, result.stderr

    def triggers():
        with sqlite3.connect(db_path) as db:
            rows = db.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        return sorted(name for (name,) in rows if name.startswith("audit_log_"))

    manage("migrate", "--noinput", "-v", "0")
    applied = triggers()
    manage("migrate", "audit", "0001", "--noinput", "-v", "0")
    reverted = triggers()
    manage("migrate", "--noinput", "-v", "0")

    assert applied == ["audit_log_append_only_delete", "audit_log_append_only_update"]
    assert reverted == []
    assert triggers() == applied
