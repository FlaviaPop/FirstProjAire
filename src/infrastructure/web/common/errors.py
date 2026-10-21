"""Error page rendering shared by `DomainErrorMiddleware` and Django's handler400/403/404/500."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

from domain.common.errors import DomainError, PolicyViolation, Violation
from infrastructure.web.common.htmx import is_htmx

GENERIC_BY_STATUS: dict[int, Promise] = {
    400: _("Your request could not be processed. Please try again."),
    403: _("You do not have access to this page."),
    404: _("We could not find this page."),
    409: _("This has already been done and cannot be repeated."),
    422: _("Please fix the following:"),
    500: _("Something went wrong on our side. Please try again later."),
}
# Extended by later stories with their own error codes (e.g. "test_already_submitted").
ERROR_MESSAGES: dict[str, str | Promise] = {}


def violation_message(violation: Violation) -> str:
    """Localized text for one violation; an unregistered code is shown as the code itself."""
    template = ERROR_MESSAGES.get(violation.code, violation.code)
    return str(template).format(**violation.params)


def render_error(request: HttpRequest, status: int, exc: DomainError | None = None) -> HttpResponse:
    """Full error page, or the HTMX partial, with the message resolved from the error code."""
    message = ERROR_MESSAGES.get(exc.code) if exc else None
    context = {
        "status": status,
        "message": message or GENERIC_BY_STATUS[status],
        "violations": [violation_message(v) for v in exc.violations]
        if isinstance(exc, PolicyViolation)
        else [],
        "request_id": getattr(request, "request_id", ""),
    }
    template = "errors/_partial.html" if is_htmx(request) else f"errors/{status}.html"
    return render(request, template, context, status=status)


def handle_400(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """handler400: malformed request (SuspiciousOperation, bad Host)."""
    return render_error(request, 400)


def handle_403(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """handler403: PermissionDenied (raised by Story 1.3's decorator)."""
    return render_error(request, 403)


def handle_404(request: HttpRequest, exception: Exception | None = None) -> HttpResponse:
    """handler404: unknown URL or Http404."""
    return render_error(request, 404)


def handle_500(request: HttpRequest) -> HttpResponse:
    """handler500: unexpected exception; the page shows only the request id as a reference."""
    return render_error(request, 500)
