"""Story 2.2: GET /<lang>/catalogue/ for every role (AC 3-5, 7-8, 11; system responses; QA rows)."""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from infrastructure.persistence.catalogue.models import GradeModel, SubjectModel
from tests.factories.accounts import UserFactory
from tests.factories.catalogue import SubjectFactory

pytestmark = pytest.mark.django_db  # seed migration from Story 2.1 is applied
NON_STUDENTS = ["teacher_client", "parent_client", "admin_client"]
EVERY_ROLE = ["student_client", *NON_STUDENTS]


def _active_ids():
    return set(SubjectModel.objects.filter(is_active=True).values_list("pk", flat=True))


def _inactive_ids():
    return set(SubjectModel.objects.filter(is_active=False).values_list("pk", flat=True))


def _main(html: str) -> str:
    return html[html.index('<main id="content"') : html.index("</main>")]


def _without_tokens(html: str) -> str:
    """The CSRF token is re-masked on every render; everything else must be identical."""
    html = re.sub(r'"X-CSRFToken": "[\w-]+"', '"X-CSRFToken": ""', html)
    return re.sub(r'name="csrfmiddlewaretoken" value="[\w-]+"', "", html)


def _section(html: str, code: str) -> str:
    start = html.index(f'<section class="catalogue__grade" aria-labelledby="grade-{code}">')
    return html[start : html.index("</section>", start)]


# --- Story Tests block ----------------------------------------------------------------------------


def test_student_sees_ten_levels_and_three_subject_links(student_client):
    html = student_client.get("/ro/catalogue/").content.decode()

    assert html.count('<h2 id="grade-') == 10
    linked = {int(i) for i in re.findall(r'href="/ro/subjects/(\d+)/"', html)}
    assert linked == _active_ids()


@pytest.mark.parametrize("fixture", NON_STUDENTS)
def test_other_roles_see_catalogue_without_subject_links(request, fixture):
    html = request.getfixturevalue(fixture).get("/en/catalogue/").content.decode()

    assert re.findall(r'href="/en/subjects/\d+/"', html) == []
    assert html.count("Available to students") == 3


def test_no_link_to_any_inactive_subject(student_client):
    html = student_client.get("/ro/catalogue/").content.decode()

    for subject_id in _inactive_ids():
        assert f"/subjects/{subject_id}/" not in html
    assert html.count('aria-disabled="true"') == len(_inactive_ids())


def test_names_are_localized(student_client):
    assert (
        "Mathematics and Environmental Exploration"
        in student_client.get("/en/catalogue/").content.decode()
    )
    assert (
        "Matematică și explorarea mediului" in student_client.get("/ro/catalogue/").content.decode()
    )


def test_catalogue_rejects_post(student_client):
    assert student_client.post("/ro/catalogue/").status_code == 405


def test_empty_catalogue_shows_empty_state(student_client):
    SubjectModel.objects.all().delete()
    GradeModel.objects.all().delete()

    response = student_client.get("/en/catalogue/")

    assert response.status_code == 200
    assert "The catalogue is not available yet." in response.content.decode()


# --- AC 3: route, guard, methods -----------------------------------------------------------------


@pytest.mark.parametrize("fixture", EVERY_ROLE)
@pytest.mark.parametrize("lang", ["ro", "en"])
def test_every_signed_in_role_gets_the_catalogue(request, fixture, lang):
    response = request.getfixturevalue(fixture).get(f"/{lang}/catalogue/")

    assert response.status_code == 200
    assert "catalogue/index.html" in [t.name for t in response.templates]


def test_anonymous_is_sent_to_login_with_next(client):
    response = client.get("/ro/catalogue/")

    assert response.status_code == 302
    assert response["Location"] == "/ro/accounts/login/?next=/ro/catalogue/"


def test_corrupt_role_is_denied(client):
    client.force_login(UserFactory(role="WIZARD"))

    assert client.get("/ro/catalogue/").status_code == 403


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_catalogue_allows_only_safe_methods(student_client, method):
    assert getattr(student_client, method)("/ro/catalogue/").status_code == 405


def test_head_is_allowed(student_client):
    assert student_client.head("/ro/catalogue/").status_code == 200


# --- AC 4: sections, headings, cards, tiles, pilot label ------------------------------------------


def test_one_labelled_section_per_level_with_its_h2(student_client):
    html = student_client.get("/ro/catalogue/").content.decode()

    sections = re.findall(r'<section class="catalogue__grade" aria-labelledby="grade-(\w+)">', html)
    headings = re.findall(r'<h2 id="grade-(\w+)">', html)
    assert sections == headings == ["K", "P", "1", "2", "3", "4", "5", "6", "7", "8"]


@pytest.mark.parametrize(
    ("lang", "names"),
    [
        ("ro", ["Grădiniță", "Clasa pregătitoare", "Clasa I", "Clasa a II-a", "Clasa a VIII-a"]),
        ("en", ["Kindergarten", "Preparatory grade", "Grade 1", "Grade 2", "Grade 8"]),
    ],
)
def test_level_headings_are_localized_and_in_order(student_client, lang, names):
    html = student_client.get(f"/{lang}/catalogue/").content.decode()

    texts = [
        re.sub(r"<[^>]+>", "", h).split()
        for h in re.findall(r'<h2 id="grade-\w+">(.*?)</h2>', html, re.S)
    ]
    labels = [" ".join(w for w in words if w != "Pilot") for words in texts]
    assert [labels[i] for i in (0, 1, 2, 3, 9)] == names


def test_heading_outline_is_h1_then_h2_per_level_then_h3_per_active_card(student_client):
    main = _main(student_client.get("/en/catalogue/").content.decode())

    levels = [int(n) for n in re.findall(r"<h([1-6])\b", main)]
    assert levels.count(1) == 1
    assert levels[0] == 1
    assert levels.count(2) == 10
    assert levels.count(3) == 3
    assert re.search(r'<h1 class="page-header__title">Catalogue</h1>', main)


def test_only_the_grade_with_active_subjects_has_the_pilot_label(student_client):
    html = student_client.get("/en/catalogue/").content.decode()

    assert html.count('class="catalogue__pilot"') == 1
    assert '<span class="catalogue__pilot">Pilot</span>' in _section(html, "2")


def test_student_cards_are_linked_ui_cards_for_clr_mem_en(student_client):
    html = student_client.get("/en/catalogue/").content.decode()
    grade_2 = _section(html, "2")

    titles = re.findall(
        r'<h3 class="card__title"><a href="/en/subjects/(\d+)/">([^<]+)</a>', grade_2
    )
    codes = dict(SubjectModel.objects.filter(is_active=True).values_list("pk", "code"))
    assert [(codes[int(i)], t) for i, t in titles] == [
        ("CLR", "Communication in Romanian"),
        ("MEM", "Mathematics and Environmental Exploration"),
        ("EN", "English"),
    ]
    assert grade_2.count('<article class="card card--link">') == 3
    assert "Available to students" not in html


@pytest.mark.parametrize("fixture", NON_STUDENTS)
def test_non_student_cards_are_informational_ui_cards(request, fixture):
    grade_2 = _section(request.getfixturevalue(fixture).get("/en/catalogue/").content.decode(), "2")

    assert grade_2.count('<article class="card">') == 3
    assert "card--link" not in grade_2
    assert grade_2.count('<p class="card__meta">Available to students</p>') == 3
    assert re.findall(r'<h3 class="card__title">([^<]+)</h3>', grade_2) == [
        "Communication in Romanian",
        "Mathematics and Environmental Exploration",
        "English",
    ]


@pytest.mark.parametrize("fixture", EVERY_ROLE)
def test_every_inactive_subject_is_a_disabled_tile_for_every_role(request, fixture):
    html = request.getfixturevalue(fixture).get("/en/catalogue/").content.decode()

    tiles = re.findall(
        r'<div class="tile tile--disabled" aria-disabled="true">(.*?)</div>', html, re.S
    )
    assert len(tiles) == len(_inactive_ids()) == 108
    assert all("Unavailable" in t and "#lock-simple" in t for t in tiles)
    assert not any(re.search(r"<a\b|<button\b|tabindex", t) for t in tiles)


def test_grade_2_mixes_three_cards_and_five_tiles_in_sort_order(student_client):
    grade_2 = _section(student_client.get("/en/catalogue/").content.decode(), "2")

    kinds = re.findall(r'<(article) class="card|<div class="tile (tile)--disabled', grade_2)
    assert ["card" if a else "tile" for a, _t in kinds] == ["card"] * 3 + ["tile"] * 5


def test_grades_and_subjects_is_the_lead_text_of_the_list(student_client):
    main = _main(student_client.get("/en/catalogue/").content.decode())

    assert '<p class="catalogue__lead">Grades and subjects</p>' in main
    assert main.index("catalogue__lead") < main.index('<section class="catalogue__grade"')


def test_catalogue_stylesheet_is_linked_after_the_layout(student_client):
    html = student_client.get("/en/catalogue/").content.decode()
    links = re.findall(r'<link rel="stylesheet" href="([^"]+)">', html)

    assert links[-2:] == ["/static/css/layout.css", "/static/css/catalogue.css"]


@pytest.mark.parametrize(
    ("fixture", "symbol"),
    [("student_client", "#list-checks-duotone"), ("teacher_client", '#list-checks"')],
)
def test_empty_state_icon_follows_the_role_theme(request, fixture, symbol):
    SubjectModel.objects.all().delete()
    GradeModel.objects.all().delete()

    main = _main(request.getfixturevalue(fixture).get("/en/catalogue/").content.decode())

    assert symbol in main
    assert "<section" not in main
    assert "catalogue__lead" not in main


# --- AC 5: no link to an inactive subject, whatever the request says ------------------------------


@pytest.mark.parametrize(
    "query", ["?can_open=1", "?role=STUDENT", "?is_active=1&subject=1", "?lang=en&can_open=true"]
)
def test_forged_query_parameters_change_nothing(teacher_client, query):
    plain = teacher_client.get("/en/catalogue/").content.decode()
    forged = teacher_client.get(f"/en/catalogue/{query}").content.decode()

    # Outside <main> only the language switcher's `next` echoes the query string.
    assert _main(forged) == _main(plain)
    assert re.findall(r'href="/en/subjects/\d+/"', forged) == []


def test_forged_query_parameters_never_link_inactive_subjects_for_students(student_client):
    html = student_client.get("/ro/catalogue/?is_active=1&can_open=1").content.decode()

    linked = {int(i) for i in re.findall(r'href="/ro/subjects/(\d+)/"', html)}
    assert linked == _active_ids()


# --- System responses: reload, writes, query count ------------------------------------------------


def test_reloads_are_identical_and_write_nothing(student_client):
    student_client.get("/ro/catalogue/")  # the first request may set the CSRF cookie

    with CaptureQueriesContext(connection) as queries:
        first = student_client.get("/ro/catalogue/")
        second = student_client.get("/ro/catalogue/")

    writes = [q["sql"] for q in queries if not q["sql"].lstrip().upper().startswith("SELECT")]
    assert (first.status_code, second.status_code) == (200, 200)
    assert _without_tokens(first.content.decode()) == _without_tokens(second.content.decode())
    assert writes == []


def test_page_query_count_does_not_grow_with_the_catalogue(student_client):
    student_client.get("/ro/catalogue/")
    with CaptureQueriesContext(connection) as before:
        student_client.get("/ro/catalogue/")
    for code in ("X1", "X2", "X3", "X4"):
        SubjectFactory(grade=GradeModel.objects.get(code="7"), code=code)

    with CaptureQueriesContext(connection) as after:
        html = student_client.get("/ro/catalogue/").content.decode()

    assert len(after) == len(before)
    assert html.count('aria-disabled="true"') == 112


def test_page_has_no_inline_script_or_style(student_client):
    html = student_client.get("/ro/catalogue/").content.decode()

    assert not re.search(r"<script(?![^>]*\bsrc=)", html)
    assert "style=" not in html
    assert "<style" not in html
    assert "https://" not in html
    assert "http://" not in html


# --- AC 11: the Student "Learn" entry appears once the route exists -------------------------------


def test_student_menu_and_home_card_link_to_the_catalogue(student_client):
    html = student_client.get("/ro/").content.decode()
    nav = html[html.index('<nav class="main-nav"') : html.index("</nav>", html.index("main-nav"))]

    assert '<a href="/ro/catalogue/">Învață</a>' in nav
    assert re.search(r'class="card__title"><a href="/ro/catalogue/">Învață</a>', _main(html))


def test_learn_is_the_current_page_on_the_catalogue(student_client):
    html = student_client.get("/en/catalogue/").content.decode()

    assert '<a href="/en/catalogue/" aria-current="page">Learn</a>' in html


@pytest.mark.parametrize("fixture", NON_STUDENTS)
def test_other_roles_menus_have_no_catalogue_entry(request, fixture):
    html = request.getfixturevalue(fixture).get("/ro/").content.decode()

    assert "/catalogue/" not in html
