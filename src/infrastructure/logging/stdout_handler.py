"""Stream handler bound to whatever `sys.stdout` is at emit time."""

import logging
import sys
from typing import TextIO


class StdoutHandler(logging.StreamHandler[TextIO]):
    """`ext://sys.stdout` would freeze the stream object seen at settings load; if stdout is
    later replaced (process supervisors, pytest's capfd) log lines would go to a stale stream.
    """

    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stdout  # handle() holds the handler lock while emit runs
        super().emit(record)
