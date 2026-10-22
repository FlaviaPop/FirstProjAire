"""Adapter: implements `application.common.audit.AuditPort` on the `audit_log` table."""

from collections.abc import Mapping

from django.contrib.auth import get_user_model

from application.common.audit import MetadataValue
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
        metadata: Mapping[str, MetadataValue] | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Store the entry; an empty `actor_username` is filled from the actor (Story 1.9).

        Raises:
            ValueError: when `metadata` contains a forbidden (sensitive) key.
        """
        data: Mapping[str, MetadataValue] = metadata or {}
        if leaked := sorted(key for key in data if is_sensitive_key(key)):
            raise ValueError(f"Forbidden audit metadata keys: {leaked}")
        target_type, target_id = target or ("", "")
        AuditLogModel.objects.create(
            actor_id=actor_id,
            actor_username=_actor_name(actor_id, actor_username),
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            metadata=dict(data),
            ip_address=ip_address,
            created_at=self._clock.now(),
        )


def _actor_name(actor_id: int | None, actor_username: str) -> str:
    # Keeps the row naming who acted after that account is deleted (actor FK -> NULL).
    if actor_username or actor_id is None:
        return actor_username
    users = get_user_model().objects.filter(pk=actor_id)
    return users.values_list("username", flat=True).first() or ""
