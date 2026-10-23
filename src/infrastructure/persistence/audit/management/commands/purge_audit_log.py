"""`manage.py purge_audit_log [--dry-run]`: the scheduled audit-log retention job (1.8 ISS-004)."""

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from infrastructure import container


class Command(BaseCommand):
    help = "Delete audit log entries older than AUDIT_RETENTION_DAYS and audit the purge."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run", action="store_true", help="Only count the entries that would be deleted."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        result = container.audit_retention().purge(dry_run=options["dry_run"])
        verb = "Would delete" if options["dry_run"] else "Deleted"
        self.stdout.write(
            f"{verb} {result.deleted} audit log entries older than {result.cutoff.isoformat()}"
        )
