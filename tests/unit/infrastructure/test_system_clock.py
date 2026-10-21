from datetime import UTC, datetime, timedelta

from domain.common.clock import Clock
from infrastructure.system_clock import SystemClock


def test_system_clock_returns_current_timezone_aware_utc_time():
    clock: Clock = SystemClock()
    before = datetime.now(UTC)

    now = clock.now()

    assert now.utcoffset() == timedelta(0)
    assert before <= now <= datetime.now(UTC)
