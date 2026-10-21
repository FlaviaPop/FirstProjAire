"""Every route is guarded or explicitly public, and the guards behave per ADR-007.

The coverage test is unmarked, so it walks the real ROOT_URLCONF. The decorator-behaviour
tests use this module's own `urlpatterns` via @pytest.mark.urls(__name__).
"""

import pytest
from django.contrib.sessions.models import Session
from django.db import connection
from django.http import HttpResponse
from django.test.utils import CaptureQueriesContext
from django.urls import URLPattern, URLResolver, get_resolver, path
from django.views import View

from domain.accounts.permissions import P
from infrastructure.web.common.decorators import (
    PUBLIC_URL_NAMES,
    require_authenticated,
    require_permission,
)
from tests.factories.accounts import UserFactory

EXEMPT_NAMESPACES = {"admin"}  # Django admin: has_permission restricted to Admin role (Story 1.9)


def _leaves(patterns, namespace=""):
    for entry in patterns:
        if isinstance(entry, URLResolver):
            ns = entry.namespace or namespace
            yield from _leaves(entry.url_patterns, ns)
        elif isinstance(entry, URLPattern):
            yield namespace, entry


def _unprotected(patterns):
    offenders = []
    for namespace, pattern in _leaves(patterns):
        if namespace in EXEMPT_NAMESPACES:
            continue
        if pattern.name is None:
            offenders.append(str(pattern.pattern))
            continue
        full_name = f"{namespace}:{pattern.name}" if namespace else pattern.name
        guarded = hasattr(pattern.callback, "required_permissions")
        if not guarded and full_name not in PUBLIC_URL_NAMES:
            offenders.append(full_name)
    return offenders


def test_every_url_is_protected_or_public():
    offenders = _unprotected(get_resolver().url_patterns)

    assert offenders == [], f"Unprotected routes: {offenders}"


@require_permission(P.CONTENT_EDIT)
def _edit(request):
    """Edit view docstring."""
    return HttpResponse("edit")


@require_permission(P.CHILD_PROGRESS_VIEW, P.CHILD_SCORES_VIEW)
def _child(request):
    return HttpResponse("child")


@require_permission(P.CHILD_PROGRESS_VIEW, P.SCORES_VIEW_ALL)
def _child_and_all(request):
    return HttpResponse("child-and-all")


@require_authenticated
def _any(request):
    return HttpResponse("any")


class _ReviewView(View):
    def get(self, request):
        return HttpResponse("review")


_review = require_permission(P.CONTENT_REVIEW)(_ReviewView.as_view())


def _unguarded(request):
    return HttpResponse("open")


urlpatterns = [
    path("edit", _edit, name="edit"),
    path("child", _child, name="child"),
    path("child-and-all", _child_and_all, name="child-and-all"),
    path("any", _any, name="any"),
    path("review", _review, name="review"),
    path("login", _any, name="login"),
]


@pytest.mark.django_db
@pytest.mark.urls(__name__)
@pytest.mark.parametrize(
    ("role", "url", "status"),
    [
        ("TEACHER", "/edit", 200),
        ("STUDENT", "/edit", 403),
        ("ADMIN", "/edit", 403),
        ("PARENT", "/edit", 403),
        ("PARENT", "/child", 200),
        ("TEACHER", "/child", 403),
        ("PARENT", "/child-and-all", 403),  # ALL keys are required
        ("ADMIN", "/review", 200),  # class-based view
        ("TEACHER", "/review", 403),
        ("STUDENT", "/any", 200),
        ("PARENT", "/any", 200),
        ("SUPERHERO", "/any", 403),  # corrupt role → denied, never granted
        ("SUPERHERO", "/edit", 403),
    ],
)
def test_decorators_enforce_role_permissions(client, role, url, status):
    client.force_login(UserFactory(role=role))

    assert client.get(url).status_code == status


@pytest.mark.django_db
@pytest.mark.urls(__name__)
@pytest.mark.parametrize("url", ["/edit?x=1", "/any?x=1"])
def test_anonymous_is_redirected_to_login_with_next(client, settings, url):
    settings.LOGIN_URL = "/login"

    response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == f"/login?next={url.replace('?', '%3F').replace('=', '%3D')}"


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_denied_request_has_no_side_effects_and_repeats_identically(client):
    student = UserFactory(role="STUDENT")
    client.force_login(student)
    sessions_before = Session.objects.count()
    last_login_before = student.last_login

    with CaptureQueriesContext(connection) as queries:
        first, second = client.get("/edit"), client.get("/edit")

    writes = [
        q["sql"]
        for q in queries
        if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    student.refresh_from_db()
    assert (first.status_code, second.status_code) == (403, 403)
    assert first.content == second.content
    assert writes == []
    assert Session.objects.count() == sessions_before
    assert student.last_login == last_login_before
    assert student.role == "STUDENT"


@pytest.mark.django_db
@pytest.mark.urls(__name__)
def test_role_cannot_be_elevated_by_request_parameters(client):
    client.force_login(UserFactory(role="STUDENT"))

    response = client.get("/edit?role=TEACHER&as=ADMIN", HTTP_X_ROLE="TEACHER")

    assert response.status_code == 403


def test_decorator_requires_at_least_one_permission():
    with pytest.raises(ValueError, match="at least one Permission"):
        require_permission()


def test_wrappers_expose_required_permissions_and_names():
    assert _edit.required_permissions == (P.CONTENT_EDIT,)
    assert _child.required_permissions == (P.CHILD_PROGRESS_VIEW, P.CHILD_SCORES_VIEW)
    assert _any.required_permissions == ()
    assert _review.required_permissions == (P.CONTENT_REVIEW,)
    assert _edit.__name__ == "_edit"
    assert _edit.__doc__ == "Edit view docstring."


def test_coverage_check_reports_unguarded_and_unnamed_routes():
    patterns = [
        path("guarded", _edit, name="guarded"),
        path("open", _unguarded, name="open"),
        path("nameless", _unguarded),
    ]

    assert _unprotected(patterns) == ["open", "nameless"]
