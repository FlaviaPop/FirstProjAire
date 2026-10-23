"""Composition root: the only module that chooses concrete implementations for ports.

One factory function per use case, grouped in one block per context (alphabetical).
"""

from django.conf import settings

from application.accounts.link_parent import LinkParent, UnlinkParent
from application.accounts.manage_account import AuditAccountChange
from application.accounts.record_security_event import RecordSecurityEvent
from application.accounts.update_preferred_language import UpdatePreferredLanguage
from infrastructure.persistence.accounts.repositories import (
    DjangoParentLinks,
    DjangoUsernameDirectory,
    DjangoUserPreferences,
)
from infrastructure.persistence.audit.fingerprint import username_fingerprint
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from infrastructure.persistence.audit.retention import AuditRetention
from infrastructure.persistence.common.unit_of_work import DjangoUnitOfWork
from infrastructure.system_clock import SystemClock

# --- accounts ------------------------------------------------------------------------------


def audit_account_change() -> AuditAccountChange:
    """Story 1.9: audit the Admin's account changes (field names only)."""
    return AuditAccountChange(DjangoAuditPort(SystemClock()), DjangoUnitOfWork())


def link_parent() -> LinkParent:
    """Story 1.9: link a Parent/Guardian to a Student (admin)."""
    return LinkParent(
        DjangoParentLinks(), DjangoAuditPort(SystemClock()), DjangoUnitOfWork(), SystemClock()
    )


def record_security_event() -> RecordSecurityEvent:
    """Story 1.8: audit sign-in, sign-out, failed sign-in and lockout events."""
    return RecordSecurityEvent(
        DjangoAuditPort(SystemClock()),
        DjangoUnitOfWork(),
        DjangoUsernameDirectory(),
        username_fingerprint,
    )


def unlink_parent() -> UnlinkParent:
    """Story 1.9: remove a parent-child link (admin); a missing link is a no-op."""
    return UnlinkParent(DjangoParentLinks(), DjangoAuditPort(SystemClock()), DjangoUnitOfWork())


def update_preferred_language() -> UpdatePreferredLanguage:
    """Story 1.4: save the signed-in user's UI language (DjangoUnitOfWork per 1.8 hand-off)."""
    return UpdatePreferredLanguage(DjangoUserPreferences(), DjangoUnitOfWork)


# --- audit ---------------------------------------------------------------------------------


def audit_retention() -> AuditRetention:
    """Story 1.8 review v1 ISS-004: the scheduled purge (`manage.py purge_audit_log`)."""
    clock = SystemClock()
    return AuditRetention(DjangoAuditPort(clock), clock, days=settings.AUDIT_RETENTION_DAYS)
