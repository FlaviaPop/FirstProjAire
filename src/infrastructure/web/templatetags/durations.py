"""Duration formatting for templates: `{% load durations %}{{ some_timedelta|minutes }}`."""

from datetime import timedelta

from django import template

register = template.Library()


@register.filter
def minutes(value: timedelta | None) -> int:
    """Whole minutes in a timedelta (rounded down; at least 1 for any positive duration).

    Used for the lockout text, so the message always matches `AXES_COOLOFF_TIME`.
    """
    if not value:
        return 0
    return max(1, int(value.total_seconds() // 60))
