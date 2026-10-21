"""Composition root: the only module that chooses concrete implementations for ports.

One factory function per use case, grouped in one block per context (alphabetical).
"""

from application.accounts.record_security_event import RecordSecurityEvent
from infrastructure.persistence.audit.repositories import DjangoAuditPort
from infrastructure.persistence.common.unit_of_work import DjangoUnitOfWork
from infrastructure.system_clock import SystemClock

# --- accounts ------------------------------------------------------------------------------


def record_security_event() -> RecordSecurityEvent:
    """Story 1.8: audit sign-in, sign-out, failed sign-in and lockout events."""
    return RecordSecurityEvent(DjangoAuditPort(SystemClock()), DjangoUnitOfWork())
