"""Production implementation of the `domain.common.clock.Clock` port."""

from datetime import datetime

from django.utils import timezone


class SystemClock:
    """Reads the wall clock through Django so tests and code agree on the time zone."""

    def now(self) -> datetime:
        return timezone.now()  # aware UTC (USE_TZ=True)
