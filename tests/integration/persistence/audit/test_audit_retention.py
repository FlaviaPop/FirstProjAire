"""Story 1.8 review v1 ISS-004: audit_log retention (owner decision: 1 year, discovery report §15).

The purge is the only code allowed past the append-only DELETE trigger, for one statement, in one
transaction that also re-creates the trigger and audits the purge itself.
"""

from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import DatabaseError, connection

from infrastructure import container
from infrastructure.persistence.audit.models import AuditLogModel
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from infrastructure.persistence.audit.retention import SYSTEM_ACTOR, AuditRetention
from tests.fakes import FixedClock

pytestmark = pytest.mark.django_db
NOW = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
CUTOFF = NOW - timedelta(days=365)
TRIGGERS = {"audit_log_append_only_delete", "audit_log_append_only_update"}


def _row(at: datetime, action: str = "auth.login") -> None:
    DjangoAuditPort(FixedClock(at)).record(action, actor_username="ana")


def _retention(audit=None) -> AuditRetention:
    return AuditRetention(audit or DjangoAuditPort(FixedClock(NOW)), FixedClock(NOW), days=365)


def _triggers() -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")
        return {name for (name,) in cursor.fetchall()} & TRIGGERS


def _actions() -> list[str]:
    return sorted(AuditLogModel.objects.values_list("action", flat=True))


def test_rows_older_than_the_retention_period_are_deleted_and_newer_ones_kept():
    _row(CUTOFF - timedelta(days=30), "old.month")
    _row(CUTOFF - timedelta(microseconds=1), "old.just")
    _row(CUTOFF, "kept.boundary")  # exactly 365 days old: kept (strictly older is purged)
    _row(NOW - timedelta(days=1), "kept.recent")

    result = _retention().purge()

    assert (result.deleted, result.cutoff) == (2, CUTOFF)
    assert _actions() == ["audit.purged", "kept.boundary", "kept.recent"]


def test_the_purge_is_itself_audited():
    _row(CUTOFF - timedelta(days=1))

    _retention().purge()

    entry = AuditLogModel.objects.get(action="audit.purged")
    assert entry.actor_id is None
    assert entry.actor_username == SYSTEM_ACTOR
    assert entry.metadata == {"deleted": 1, "cutoff": CUTOFF.isoformat()}
    assert entry.created_at == NOW


def test_a_purge_with_nothing_to_delete_is_still_audited():
    _row(NOW)

    result = _retention().purge()

    assert result.deleted == 0
    assert AuditLogModel.objects.get(action="audit.purged").metadata["deleted"] == 0


def test_dry_run_counts_without_deleting_or_auditing():
    _row(CUTOFF - timedelta(days=1))
    _row(NOW)

    result = _retention().purge(dry_run=True)

    assert result.deleted == 1
    assert AuditLogModel.objects.count() == 2
    assert not AuditLogModel.objects.filter(action="audit.purged").exists()


def test_both_append_only_triggers_are_in_place_after_a_purge():
    _row(CUTOFF - timedelta(days=1))
    _row(NOW)

    _retention().purge()

    assert _triggers() == TRIGGERS
    row = AuditLogModel.objects.filter(action="auth.login").get()
    with pytest.raises(DatabaseError, match="append-only"), connection.cursor() as cursor:
        cursor.execute("DELETE FROM audit_log WHERE id = %s", [row.pk])
    with pytest.raises(DatabaseError, match="append-only"), connection.cursor() as cursor:
        cursor.execute("UPDATE audit_log SET action = 'x' WHERE id = %s", [row.pk])


class _FailingAudit:
    def record(self, action, **kwargs):
        raise DatabaseError("disk full")


def test_a_failed_purge_rolls_back_rows_and_triggers():
    _row(CUTOFF - timedelta(days=1), "old.row")

    with pytest.raises(DatabaseError, match="disk full"):
        _retention(_FailingAudit()).purge()

    assert _actions() == ["old.row"]
    assert _triggers() == TRIGGERS


def test_retention_days_must_be_a_positive_whole_number():
    with pytest.raises(ValueError, match="positive"):
        AuditRetention(DjangoAuditPort(FixedClock(NOW)), FixedClock(NOW), days=0)


def test_container_builds_the_retention_from_settings(settings):
    settings.AUDIT_RETENTION_DAYS = 30

    retention = container.audit_retention()

    assert isinstance(retention, AuditRetention)
    assert retention.days == 30


def test_one_year_is_the_configured_retention():
    from django.conf import settings

    assert settings.AUDIT_RETENTION_DAYS == 365


def test_command_purges_and_reports(settings):
    settings.AUDIT_RETENTION_DAYS = 365
    _row(datetime.now(UTC) - timedelta(days=400), "old.row")
    _row(datetime.now(UTC), "new.row")
    out = StringIO()

    call_command("purge_audit_log", stdout=out)

    assert _actions() == ["audit.purged", "new.row"]
    assert out.getvalue().startswith("Deleted 1 audit log entries older than ")


def test_command_dry_run_reports_without_deleting(settings):
    settings.AUDIT_RETENTION_DAYS = 365
    _row(datetime.now(UTC) - timedelta(days=400), "old.row")
    out = StringIO()

    call_command("purge_audit_log", "--dry-run", stdout=out)

    assert _actions() == ["old.row"]
    assert out.getvalue().startswith("Would delete 1 audit log entries older than ")
