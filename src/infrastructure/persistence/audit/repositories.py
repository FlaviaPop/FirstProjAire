"""Adapter: implements `application.common.audit.AuditPort` on the `audit_log` table."""

from collections.abc import Mapping

from domain.common.clock import Clock
from infrastructure.logging.sensitive import is_sensitive_key
from infrastructure.persistence.audit.models import AuditLogModel

# Patterns §9 "never log" list, applied to audit metadata too (Story 1.8 review v1 ISS-001).
# The rule is shared with the JSON logs: see infrastructure.logging.sensitive.


class DjangoAuditPort:
    """Append one `AuditLogModel` row per call; timestamps come from the injected clock."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock

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
        """Store the entry.

        Raises:
            ValueError: when `metadata` contains a forbidden (sensitive) key.
        """
        data: Mapping[str, str | int | bool] = metadata or {}
        if leaked := sorted(key for key in data if is_sensitive_key(key)):
            raise ValueError(f"Forbidden audit metadata keys: {leaked}")
        target_type, target_id = target or ("", "")
        AuditLogModel.objects.create(
            actor_id=actor_id,
            actor_username=actor_username,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=dict(data),
            ip_address=ip_address,
            created_at=self._clock.now(),
        )
