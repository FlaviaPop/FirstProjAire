"""Audit-log retention (Story 1.8 review v1 ISS-004; owner decision: keep 1 year).

The only code allowed past the append-only DELETE trigger. In ONE transaction it drops that
trigger, deletes the rows older than the cutoff with one statement, re-creates the trigger and
audits the purge itself. SQLite DDL is transactional, so any failure rolls everything back with
the trigger in place, and the IMMEDIATE transaction holds the write lock throughout, so nothing
else can delete in between. The UPDATE trigger and the ORM guards are never touched.
"""

import importlib
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import connection, transaction

from application.common.audit import AuditPort
from domain.common.clock import Clock
from infrastructure.persistence.audit.models import AuditLogModel

# The trigger SQL lives in the migration (migrations stay self-contained); reuse it, never copy.
_TRIGGERS = importlib.import_module(
    "infrastructure.persistence.audit.migrations.0002_append_only_triggers"
)
_CREATE_DELETE_TRIGGER = next(sql for sql in _TRIGGERS.CREATE_TRIGGERS if "BEFORE DELETE" in sql)
# No IF EXISTS: a missing trigger means the schema is not what this code expects, so fail.
_DROP_DELETE_TRIGGER = "DROP TRIGGER audit_log_append_only_delete;"
_DELETE_OLDER = "DELETE FROM audit_log WHERE created_at < %s"
# Usernames cannot contain parentheses, so this never names a real account.
SYSTEM_ACTOR = "(system)"


@dataclass(frozen=True)
class PurgeResult:
    cutoff: datetime
    deleted: int


class AuditRetention:
    """Deletes audit entries older than `days`, auditing each purge as `audit.purged`."""

    def __init__(self, audit: AuditPort, clock: Clock, *, days: int) -> None:
        if isinstance(days, bool) or not isinstance(days, int) or days < 1:
            raise ValueError(f"Retention days must be a positive whole number, got {days!r}")
        self._audit = audit
        self._clock = clock
        self.days = days

    def purge(self, *, dry_run: bool = False) -> PurgeResult:
        """Delete (or with `dry_run`, only count) the entries strictly older than the cutoff."""
        cutoff = self._clock.now() - timedelta(days=self.days)
        if dry_run:
            return PurgeResult(cutoff, AuditLogModel.objects.filter(created_at__lt=cutoff).count())
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(_DROP_DELETE_TRIGGER)
            cursor.execute(_DELETE_OLDER, [connection.ops.adapt_datetimefield_value(cutoff)])
            deleted = cursor.rowcount
            cursor.execute(_CREATE_DELETE_TRIGGER)
            self._audit.record(
                "audit.purged",
                actor_username=SYSTEM_ACTOR,
                metadata={"deleted": deleted, "cutoff": cutoff.isoformat()},
            )
        return PurgeResult(cutoff, deleted)
