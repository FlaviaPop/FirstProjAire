from datetime import UTC, datetime


class FixedClock:
    """`Clock` fake that always returns the same aware UTC instant."""

    def __init__(self, at: datetime = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at
