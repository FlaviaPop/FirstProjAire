"""Adapter: implements `application.common.audit.AuditPort` on the `audit_log` table."""

from collections.abc import Mapping

from domain.common.clock import Clock
from infrastructure.persistence.audit.models import AuditLogModel

# Patterns §9 "never log" list, applied to audit metadata as well. Matched as *fragments* of a
# case-folded key (review v1 ISS-001): "new_password", "Token", "user_dob" are all rejected.
# The log is append-only, so a leaked value could never be removed by the application.
FORBIDDEN_METADATA_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "birth",
    "dob",
    "answer",
    "response",
)


def is_sensitive_metadata_key(key: str) -> bool:
    """True if `key` names a password, secret, date of birth or test answer, in any spelling."""
    normalised = key.casefold().replace("-", "_")
    return any(fragment in normalised for fragment in FORBIDDEN_METADATA_FRAGMENTS)


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
        if leaked := sorted(key for key in data if is_sensitive_metadata_key(key)):
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
