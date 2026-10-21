class FakeAuditPort:
    """In-memory `AuditPort`: every call is appended to `records` as a plain dict."""

    def __init__(self) -> None:
        self.records: list[dict] = []

    def record(
        self,
        action,
        *,
        actor_id=None,
        actor_username="",
        target=None,
        metadata=None,
        ip_address=None,
    ):
        self.records.append(
            {
                "action": action,
                "actor_id": actor_id,
                "actor_username": actor_username,
                "target": target,
                "metadata": dict(metadata or {}),
                "ip_address": ip_address,
            }
        )
