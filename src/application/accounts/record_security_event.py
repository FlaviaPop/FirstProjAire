"""Record authentication events (sign-in, sign-out, failures, lockouts) in the audit log."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from application.common.audit import AuditPort
from application.common.unit_of_work import UnitOfWork

MAX_USERNAME = 150  # matches AuditLogModel.actor_username / UserModel.username
EMPTY_USERNAME = "(empty)"
UNKNOWN_PREFIX = "(unknown):"


class SecurityEvent(StrEnum):
    """Audit action names for authentication events."""

    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    LOCKOUT = "auth.lockout"


class UsernameDirectory(Protocol):
    """Answers whether a typed username belongs to a real account."""

    def exists(self, username: str) -> bool: ...


Fingerprint = Callable[[str], str]
"""Short, non-reversible, keyed digest of a string (correlates repeats without storing it)."""


@dataclass(frozen=True)
class SecurityEventCommand:
    """One authentication event. Identity fields come from the auth framework, not user input."""

    event: SecurityEvent
    username: str
    user_id: int | None = None
    ip_address: str | None = None


class RecordSecurityEvent:
    """Write exactly one audit entry per authentication event, inside one unit of work."""

    def __init__(
        self,
        audit: AuditPort,
        uow: UnitOfWork,
        directory: UsernameDirectory,
        fingerprint: Fingerprint,
    ) -> None:
        self._audit, self._uow = audit, uow
        self._directory, self._fingerprint = directory, fingerprint

    def execute(self, cmd: SecurityEventCommand) -> None:
        """Record `cmd` with a safe actor name (see `_actor_username`)."""
        with self._uow:
            self._audit.record(
                cmd.event.value,
                actor_id=cmd.user_id,
                actor_username=self._actor_username(cmd)[:MAX_USERNAME],
                ip_address=cmd.ip_address,
            )

    def _actor_username(self, cmd: SecurityEventCommand) -> str:
        """The name to store, never a possibly mistyped password (Story 1.8 review v1 ISS-003).

        - Signed-in events (a known `user_id`): the account's username.
        - Failed or locked-out attempts: the typed text only if it is a real account's username;
          otherwise "(unknown):<fingerprint>" so repeated attempts can still be correlated.
        - An empty typed username: "(empty)".
        """
        if cmd.user_id is not None:
            return cmd.username or EMPTY_USERNAME
        if not cmd.username:
            return EMPTY_USERNAME
        if self._directory.exists(cmd.username):
            return cmd.username
        return f"{UNKNOWN_PREFIX}{self._fingerprint(cmd.username)}"
