"""Record authentication events (sign-in, sign-out, failures, lockouts) in the audit log."""

from dataclasses import dataclass
from enum import StrEnum

from application.common.audit import AuditPort
from application.common.unit_of_work import UnitOfWork

MAX_USERNAME = 150  # matches AuditLogModel.actor_username / UserModel.username
EMPTY_USERNAME = "(empty)"


class SecurityEvent(StrEnum):
    """Audit action names for authentication events."""

    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    LOCKOUT = "auth.lockout"


@dataclass(frozen=True)
class SecurityEventCommand:
    """One authentication event. Identity fields come from the auth framework, not user input."""

    event: SecurityEvent
    username: str
    user_id: int | None = None
    ip_address: str | None = None


class RecordSecurityEvent:
    """Write exactly one audit entry per authentication event, inside one unit of work."""

    def __init__(self, audit: AuditPort, uow: UnitOfWork) -> None:
        self._audit, self._uow = audit, uow

    def execute(self, cmd: SecurityEventCommand) -> None:
        """Record `cmd`; an empty username (e.g. a blank failed login) is stored as "(empty)"."""
        username = (cmd.username or EMPTY_USERNAME)[:MAX_USERNAME]
        with self._uow:
            self._audit.record(
                cmd.event.value,
                actor_id=cmd.user_id,
                actor_username=username,
                ip_address=cmd.ip_address,
            )
