"""Story 2.2: GET /<lang>/subjects/<id>/ (AC 2, 3, 6, 10; RBAC table; system responses)."""

import logging
import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve

from domain.accounts.permissions import P
from infrastructure.persistence.catalogue.models import SubjectModel

pytestmark = pytest.mark.django_db
NON_STUDENTS = ["teacher_client", "parent_client", "admin_client"]


def _active_ids():
    return set(SubjectModel.objects.filter(is_active=True).values_list("pk", flat=True))


def _inactive_ids():
    return set(SubjectModel.objects.filter(is_active=False).values_list("pk", flat=True))


def _id(code: str) -> int:
    return SubjectModel.objects.get(grade__code="2", code=code).pk


def _main(html: str) -> str:
    return html[html.index('<main id="content"') : html.index("</main>")]


def _without_tokens(html: str) -> str:
    html = re.sub(r'"X-CSRFToken": "[\w-]+"', '"X-CSRFToken": ""', html)
    return re.sub(r'name="csrfmiddlewaretoken" value="[\w-]+"', "", html)


# --- Story Tests block ----------------------------------------------------------------------------


def test_student_opens_active_subject_with_breadcrumb_and_empty_state(student_client):
    subject_id = min(_active_ids())

    response = student_client.get(f"/en/subjects/{subject_id}/")

    html = response.content.decode()
    assert response.status_code == 200
    assert 'aria-label="Breadcrumb"' in html
    assert 'aria-current="page"' in html
    assert "No chapters are published yet." in html


def test_inactive_and_unknown_subjects_are_identical_404s(student_client):
    inactive = student_client.get(f"/ro/subjects/{min(_inactive_ids())}/")
    unknown = student_client.get("/ro/subjects/999999/")

    assert inactive.status_code == unknown.status_code == 404
    assert [t.name for t in inactive.templates][:1] == [t.name for t in unknown.templates][:1]


@pytest.mark.parametrize("fixture", NON_STUDENTS)
def test_non_students_get_403_on_subject_page(request, fixture):
    subject_id = min(_active_ids())

    assert request.getfixturevalue(fixture).get(f"/ro/subjects/{subject_id}/").status_code == 403


def test_anonymous_subject_page_redirects_to_login(client):
    response = client.get(f"/ro/subjects/{min(_active_ids())}/")

    assert response.status_code == 302
    assert "/ro/accounts/login/" in response["Location"]


# --- AC 3: route and guard ------------------------------------------------------------------------


def test_route_name_and_permission_are_declared():
    match = resolve(f"/ro/subjects/{_id('MEM')}/")

    assert match.view_name == "catalogue:subject"
    assert match.kwargs == {"subject_id": _id("MEM")}
    assert match.func.required_permissions == (P.LESSONS_VIEW,)
    assert resolve("/ro/catalogue/").func.required_permissions == ()


def test_anonymous_redirect_keeps_the_subject_as_next(client):
    subject_id = _id("EN")

    response = client.get(f"/en/subjects/{subject_id}/")

    assert response["Location"] == f"/en/accounts/login/?next=/en/subjects/{subject_id}/"


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_subject_page_allows_only_safe_methods(student_client, method):
    assert getattr(student_client, method)(f"/ro/subjects/{_id('CLR')}/").status_code == 405


# --- AC 10 / QA: every id, every role -------------------------------------------------------------


def test_every_active_subject_opens_for_the_student(student_client):
    for subject_id in _active_ids():
        assert student_client.get(f"/ro/subjects/{subject_id}/").status_code == 200


def test_every_inactive_subject_is_404_for_the_student(student_client):
    statuses = {student_client.get(f"/ro/subjects/{i}/").status_code for i in _inactive_ids()}

    assert statuses == {404}
    assert len(_inactive_ids()) == 108


@pytest.mark.parametrize("fixture", NON_STUDENTS)
def test_every_active_subject_is_403_for_other_roles(request, fixture):
    client = request.getfixturevalue(fixture)

    assert {client.get(f"/en/subjects/{i}/").status_code for i in _active_ids()} == {403}


@pytest.mark.parametrize("fixture", NON_STUDENTS)
def test_role_denial_comes_before_the_existence_check(request, fixture):
    client = request.getfixturevalue(fixture)

    inactive = client.get(f"/en/subjects/{min(_inactive_ids())}/")
    unknown = client.get("/en/subjects/999999/")

    assert inactive.status_code == unknown.status_code == 403


@pytest.mark.parametrize("path", ["/ro/subjects/abc/", "/ro/subjects/-1/", "/ro/subjects/1.5/"])
def test_non_numeric_id_matches_no_route(student_client, path):
    response = student_client.get(path)

    assert response.status_code == 404
    assert "errors/404.html" in [t.name for t in response.templates]


# --- AC 2: identical 404 for inactive and unknown, logged as not_found ----------------------------


def test_inactive_and_unknown_404_pages_are_byte_identical(student_client):
    hidden_path = f"/en/subjects/{min(_inactive_ids())}/"
    inactive = student_client.get(hidden_path).content.decode()
    unknown = student_client.get("/en/subjects/999999/").content.decode()

    # Only the language switcher's `next` (the requested path) differs outside <main>.
    assert _main(inactive) == _main(unknown)
    assert _without_tokens(inactive).replace(hidden_path, "/en/subjects/N/") == _without_tokens(
        unknown
    ).replace("/en/subjects/999999/", "/en/subjects/N/")
    assert "Page not found" in inactive


def test_hidden_subject_404_is_logged_as_not_found(student_client, caplog):
    caplog.set_level(logging.INFO, logger="infrastructure.web.common.middleware")

    student_client.get(f"/ro/subjects/{min(_inactive_ids())}/")
    student_client.get("/ro/subjects/999999/")

    events = [
        (r.code, r.status)
        for r in caplog.records
        if r.name == "infrastructure.web.common.middleware" and r.getMessage() == "domain_error"
    ]
    assert events == [("not_found", 404), ("not_found", 404)]


@pytest.mark.parametrize("query", ["?is_active=1", "?active=true&role=TEACHER", "?preview=1"])
def test_forged_query_parameters_cannot_open_an_inactive_subject(student_client, query):
    subject_id = min(_inactive_ids())

    assert student_client.get(f"/ro/subjects/{subject_id}/{query}").status_code == 404


@pytest.mark.parametrize("query", ["?role=STUDENT", "?can_open=1"])
def test_forged_query_parameters_cannot_lift_the_role_denial(teacher_client, query):
    assert teacher_client.get(f"/ro/subjects/{_id('MEM')}/{query}").status_code == 403


# --- AC 6: page content ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("lang", "crumbs", "title"),
    [
        (
            "ro",
            [("/ro/catalogue/", "Catalog"), ("", "Clasa a II-a")],
            "Matematică și explorarea mediului",
        ),
        (
            "en",
            [("/en/catalogue/", "Catalogue"), ("", "Grade 2")],
            "Mathematics and Environmental Exploration",
        ),
    ],
)
def test_breadcrumb_is_catalogue_then_grade_then_subject(
    student_client, compiled_catalogues, lang, crumbs, title
):
    html = student_client.get(f"/{lang}/subjects/{_id('MEM')}/").content.decode()

    items = re.findall(
        r'<li class="breadcrumb__item"( aria-current="page")?>(.*?)</li>', html, re.S
    )
    assert len(items) == 3
    first_link = re.search(r'<a href="([^"]+)">([^<]+)</a>', items[0][1])
    assert (first_link.group(1), first_link.group(2)) == crumbs[0]
    assert "<a " not in items[1][1]
    assert items[1][1].strip().endswith(crumbs[1][1])
    assert items[2] == (' aria-current="page"', items[2][1])
    assert "<a " not in items[2][1]
    assert items[2][1].strip().endswith(title)
    assert f'<h1 class="page-header__title">{title}</h1>' in html
    assert f"<title>{title}</title>" in html


def test_subject_page_shows_the_empty_chapter_list_with_the_student_icon(student_client):
    html = student_client.get(f"/en/subjects/{_id('EN')}/").content.decode()

    assert '<p class="empty-state__message">No chapters are published yet.</p>' in html
    assert "#list-checks-duotone" in html


def test_subject_page_reloads_are_identical_and_write_nothing(student_client):
    url = f"/ro/subjects/{_id('CLR')}/"
    student_client.get(url)

    with CaptureQueriesContext(connection) as queries:
        first, second = student_client.get(url), student_client.get(url)

    assert _without_tokens(first.content.decode()) == _without_tokens(second.content.decode())
    assert all(q["sql"].lstrip().upper().startswith("SELECT") for q in queries)


def test_subject_page_has_no_inline_script_or_style(student_client):
    html = student_client.get(f"/ro/subjects/{_id('MEM')}/").content.decode()

    assert not re.search(r"<script(?![^>]*\bsrc=)", html)
    assert "style=" not in html
    assert "<style" not in html
