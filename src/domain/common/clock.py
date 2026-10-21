"""Clock port: the single source of "now", so time-dependent rules stay testable."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Returns the current instant as a timezone-aware datetime."""

    def now(self) -> datetime: ...
