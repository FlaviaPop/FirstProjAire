from datetime import timedelta

import pytest

from infrastructure.web.templatetags.durations import minutes


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, 0),
        (timedelta(0), 0),
        (timedelta(seconds=30), 1),  # any positive duration shows at least 1 minute
        (timedelta(seconds=90), 1),  # rounded down
        (timedelta(minutes=15), 15),
        (timedelta(hours=1), 60),
    ],
)
def test_minutes_filter(value, expected):
    assert minutes(value) == expected
