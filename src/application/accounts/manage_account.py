"""Audit the Admin's account changes (create, update, delete, password, role, unlock).

Only field NAMES cross this boundary: callers pass `form.changed_data`, never values, so a date
of birth or a password can't reach the audit log (patterns §9, requirements privacy).
"""

from collections.abc import Iterable, Mapping

from application.common.audit import AuditPort
from application.common.unit_of_work import UnitOfWork

LOCKOUT_CLEARED = "auth.lockout_cleared"
ACCOUNT_ACTIONS = frozenset(
    {
        "accounts.created",
        "accounts.updated",
        "accounts.deleted",
        "accounts.password_changed",
        "accounts.role_changed",
        # Owner decision 2026-10-22: unlocking is an account change, with no fields metadata.
        LOCKOUT_CLEARED,
    }
)
# The creation form's two password inputs; a password change is its own action.
PASSWORD_FORM_FIELDS = frozenset({"password1", "password2"})
MAX_TARGET_ID = 64  # AuditLogModel.target_id


class AuditAccountChange:
    """Record one account change in the audit log, inside its own unit of work."""

    def __init__(self, audit: AuditPort, uow: UnitOfWork) -> None:
        self._audit, self._uow = audit, uow

    def execute(
        self,
        action: str,
        actor_id: int,
        target_user_id: int | None,
        target_username: str,
        changed_fields: Iterable[str] = (),
    ) -> None:
        """Record `action` by `actor_id` on one account.

        Args:
            action: One of `ACCOUNT_ACTIONS`.
            actor_id: The acting Admin (`request.user.pk`).
            target_user_id: The account's id; None when no account matches (lockouts only).
            target_username: Target label used when there is no id (never a raw typed name).
            changed_fields: Names of the changed form fields; values are never accepted.

        Raises:
            ValueError: for an action outside `ACCOUNT_ACTIONS`.
        """
        if action not in ACCOUNT_ACTIONS:
            raise ValueError(f"Unknown account audit action: {action!r}")
        target_id = str(target_user_id) if target_user_id is not None else target_username
        with self._uow:
            self._audit.record(
                action,
                actor_id=actor_id,
                target=("user", target_id[:MAX_TARGET_ID]),
                metadata=_metadata(action, changed_fields),
            )


def _metadata(action: str, changed_fields: Iterable[str]) -> Mapping[str, list[str]] | None:
    if action == LOCKOUT_CLEARED:
        return None
    return {"fields": sorted(set(changed_fields) - PASSWORD_FORM_FIELDS)}
