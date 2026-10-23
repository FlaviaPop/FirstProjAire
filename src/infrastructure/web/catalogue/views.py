"""GET /<lang>/catalogue/ and /<lang>/subjects/<id>/ (Story 2.2): read-only, via the query service.

`@require_safe` is the outermost decorator: `functools.wraps` copies the guard's
`required_permissions` onto it, which the URL-coverage test reads.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext
from django.views.decorators.http import require_safe

from domain.accounts.permissions import Permission, has_permission
from domain.accounts.roles import Role
from infrastructure.persistence.catalogue.queries import (
    SubjectDTO,
    active_subject,
    catalogue_overview,
)
from infrastructure.web.common.decorators import require_authenticated, require_permission
from infrastructure.web.common.i18n import localized

Breadcrumbs = list[tuple[str, str]]


def _role(request: HttpRequest) -> Role:
    # The guards already rejected anonymous users and unknown roles (403), so this can't fail.
    return Role(getattr(request.user, "role", ""))


def _icon_variant(role: Role) -> str:
    return "duotone" if role is Role.STUDENT else "regular"


def _breadcrumbs(subject: SubjectDTO, title: str) -> Breadcrumbs:
    """Catalogue (link), then the grade, then the subject (the current page)."""
    return [
        (gettext("Catalogue"), reverse("catalogue:index")),
        (localized(subject, "grade_name"), ""),
        (title, ""),
    ]


@require_safe
@require_authenticated
def index(request: HttpRequest) -> HttpResponse:
    """GET /<lang>/catalogue/ — any signed-in role; subject links only with lessons:view."""
    role = _role(request)
    context = {
        "grades": catalogue_overview(),
        # From the session user only; request parameters never decide who may follow links.
        "can_open": has_permission(role, Permission.LESSONS_VIEW),
        "icon_variant": _icon_variant(role),
    }
    return render(request, "catalogue/index.html", context)


@require_safe
@require_permission(Permission.LESSONS_VIEW)
def subject(request: HttpRequest, subject_id: int) -> HttpResponse:
    """GET /<lang>/subjects/<id>/ — lessons:view; inactive or unknown → NotFound (404)."""
    found = active_subject(subject_id)  # NotFound -> DomainErrorMiddleware -> 404 page
    title = localized(found, "name")
    context = {
        "subject": found,
        "title": title,
        "breadcrumbs": _breadcrumbs(found, title),
        "icon_variant": _icon_variant(_role(request)),
    }
    return render(request, "catalogue/subject.html", context)
