"""The only HTMX request detector in the codebase (patterns §7.4)."""

from django.http import HttpRequest


def is_htmx(request: HttpRequest) -> bool:
    """True for requests issued by HTMX (header HX-Request: true)."""
    return request.headers.get("HX-Request") == "true"
