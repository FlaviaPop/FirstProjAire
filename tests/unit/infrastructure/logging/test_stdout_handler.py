import io
import logging
import sys

from infrastructure.logging.stdout_handler import StdoutHandler


def test_handler_writes_to_the_current_stdout_even_if_it_was_replaced(monkeypatch):
    handler = StdoutHandler()
    replacement = io.StringIO()
    monkeypatch.setattr(sys, "stdout", replacement)

    handler.emit(logging.makeLogRecord({"msg": "probe"}))

    assert replacement.getvalue() == "probe\n"
