"""Audit port: the business record of who did what (patterns §9 — separate from logs)."""

from collections.abc import Mapping
from typing import Protocol


class AuditPort(Protocol):
    """Appends one entry to the audit log. Implementations never update or delete entries."""

    def record(
        self,
        action: str,
        *,
        actor_id: int | None = None,
        actor_username: str = "",
        target: tuple[str, str] | None = None,
        metadata: Mapping[str, str | int | bool] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Record one action.

        Args:
            action: Stable dotted event name, e.g. "auth.login".
            actor_id: The acting user's id, or None for unknown/anonymous actors.
            actor_username: Kept even after the account is deleted.
            target: `(target_type, target_id)` of the affected record, if any.
            metadata: Small non-sensitive context; passwords, DOBs and answers are forbidden.
            ip_address: Client address as resolved by the web layer.
        """
        ...
