"""Adapter: implements `application.common.audit.AuditPort` on the `audit_log` table."""

from collections.abc import Mapping

from domain.common.clock import Clock
from infrastructure.persistence.audit.models import AuditLogModel

# Patterns §9 "never log" list, applied to audit metadata as well.
FORBIDDEN_METADATA_KEYS = frozenset(
    {"password", "date_of_birth", "dob", "answer", "answers", "response", "token"}
)


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
        if leaked := FORBIDDEN_METADATA_KEYS & set(data):
            raise ValueError(f"Forbidden audit metadata keys: {sorted(leaked)}")
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
