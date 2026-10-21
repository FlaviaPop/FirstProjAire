from datetime import UTC, datetime

from domain.common.clock import Clock


class _FixedClock:
    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


def test_any_object_with_now_satisfies_the_clock_port():
    instant = datetime(2026, 10, 21, 9, 0, tzinfo=UTC)

    clock: Clock = _FixedClock(instant)

    assert clock.now() == instant
