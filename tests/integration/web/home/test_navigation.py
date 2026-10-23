"""Story 1.7: the NAV_BY_ROLE registry, available_sections and the menu/card tags."""

import re
from types import SimpleNamespace

import pytest
from django.urls import resolve

from domain.accounts.permissions import ROLE_PERMISSIONS, P
from domain.accounts.roles import Role
from infrastructure.web.home.navigation import NAV_BY_ROLE, NavEntry, available_sections

pytestmark = pytest.mark.django_db
ROLE_FIXTURES = {
    Role.STUDENT: "student_client",
    Role.TEACHER: "teacher_client",
    Role.PARENT: "parent_client",
    Role.ADMIN: "admin_client",
}


# --- Story Tests block ----------------------------------------------------------------------------


@pytest.mark.parametrize("role", list(Role))
def test_every_rendered_link_is_permitted_for_the_role(request, role):
    html = request.getfixturevalue(ROLE_FIXTURES[role]).get("/ro/").content.decode()
    nav_and_cards = re.findall(r'href="(/ro/[^"#?]*)"', html)

    assert nav_and_cards
    for href in nav_and_cards:
        match = resolve(href)
        required = set(getattr(match.func, "required_permissions", ()))
        if match.namespace == "admin":
            assert role is Role.ADMIN
        else:
            assert required <= set(ROLE_PERMISSIONS[role]), f"{role} sees forbidden link {href}"


def test_student_never_sees_staff_links(student_client):
    html = student_client.get("/ro/").content.decode()

    assert not re.search(r'href="/ro/(admin|teach|manage|scores)/', html)


def test_unresolvable_entries_are_skipped_not_raised(student_client):
    # progress:me ships in CYCLE-3; the page must still render.
    assert student_client.get("/ro/").status_code == 200


def test_current_page_is_marked(student_client):
    assert 'aria-current="page"' in student_client.get("/ro/").content.decode()


# --- AC 4: the registry, exactly and in order -----------------------------------------------------


def _shape(role: Role) -> list[tuple[str, P | None]]:
    return [(entry.url_name, entry.permission) for entry in NAV_BY_ROLE[role]]


def test_registry_entries_per_role_match_the_story():
    home = ("home:index", None)

    assert _shape(Role.STUDENT) == [
        home,
        ("catalogue:index", P.LESSONS_VIEW),
        ("progress:me", P.SCORES_VIEW_OWN),
    ]
    assert _shape(Role.TEACHER) == [
        home,
        ("content:teacher_dashboard", P.CONTENT_EDIT),
        ("progress:scores", P.SCORES_VIEW_ALL),
        ("notifications:list", P.CONTENT_EDIT),
    ]
    assert _shape(Role.PARENT) == [home, ("progress:children", P.CHILD_PROGRESS_VIEW)]
    assert _shape(Role.ADMIN) == [
        home,
        ("admin:index", P.ACCOUNTS_MANAGE),
        ("moderation:queue", P.CONTENT_REVIEW),
        ("progress:scores", P.SCORES_VIEW_ALL),
        ("reporting:pilot", P.ACCOUNTS_MANAGE),
    ]


@pytest.mark.parametrize("role", list(Role))
def test_every_registry_entry_is_permitted_for_its_role(role):
    for entry in NAV_BY_ROLE[role]:
        assert entry.permission is None or entry.permission in ROLE_PERMISSIONS[role]


@pytest.mark.parametrize("role", list(Role))
def test_every_entry_has_a_known_icon(role):
    from infrastructure.web.templatetags.ui import ICON_NAMES

    assert all(entry.icon in ICON_NAMES for entry in NAV_BY_ROLE[role])


# --- AC 5: available_sections ---------------------------------------------------------------------


def test_available_sections_keeps_only_resolvable_routes():
    sections = available_sections(SimpleNamespace(role="ADMIN"))

    # Moderation, Scores and Pilot ship in CYCLE-3: skipped until their routes exist.
    assert [entry.url_name for entry, _url in sections] == ["home:index", "admin:index"]
    assert [url for _entry, url in sections] == ["/ro/", "/ro/admin/"]


@pytest.mark.parametrize("role", ["", "WIZARD", None, "student"])
def test_available_sections_is_empty_for_an_invalid_role(role):
    assert available_sections(SimpleNamespace(role=role)) == ()


def test_available_sections_filters_by_permission(monkeypatch):
    forbidden = NavEntry("Accounts", "admin:index", P.ACCOUNTS_MANAGE, "shield-check")
    monkeypatch.setitem(NAV_BY_ROLE, Role.STUDENT, (*NAV_BY_ROLE[Role.STUDENT], forbidden))

    urls = [entry.url_name for entry, _url in available_sections(SimpleNamespace(role="STUDENT"))]

    assert "admin:index" not in urls


def test_available_sections_never_raises_for_unknown_url_names(monkeypatch):
    ghost = NavEntry("Ghost", "nowhere:at_all", None, "compass")
    monkeypatch.setitem(NAV_BY_ROLE, Role.STUDENT, (ghost,))

    assert available_sections(SimpleNamespace(role="STUDENT")) == ()


def test_anonymous_user_has_no_sections():
    from django.contrib.auth.models import AnonymousUser

    assert available_sections(AnonymousUser()) == ()


# --- AC 3 / 7: menu and cards come from the same registry -----------------------------------------


@pytest.mark.parametrize("role", list(Role))
def test_menu_and_cards_list_the_same_sections(request, role):
    html = request.getfixturevalue(ROLE_FIXTURES[role]).get("/ro/").content.decode()
    nav = html[html.index('<nav class="main-nav"') : html.index("</nav>", html.index("main-nav"))]
    main = html[html.index('<main id="content"') :]
    nav_hrefs = re.findall(r'href="([^"]+)"', nav)
    card_hrefs = re.findall(r'class="card__title"><a href="([^"]+)"', main)

    assert nav_hrefs[0] == "/ro/"
    assert card_hrefs == nav_hrefs[1:]


def test_only_the_current_link_is_marked(admin_client):
    html = admin_client.get("/ro/").content.decode()
    nav = html[html.index('<nav class="main-nav"') : html.index("</nav>", html.index("main-nav"))]

    assert re.findall(r'<a href="([^"]+)" aria-current="page"', nav) == ["/ro/"]
    assert nav.count('aria-current="page"') == 1


# --- Defensive tag paths -------------------------------------------------------------------------


class _UnreadableMessages:
    def __iter__(self):
        from django.db import OperationalError

        raise OperationalError("database is locked")

    def __bool__(self):
        return True


def test_shell_messages_are_empty_when_the_session_is_unreadable(rf):
    from django.template import Context, Template

    html = Template(
        "{% load navigation %}{% shell_messages as flash %}[{{ flash|length }}]"
    ).render(Context({"request": rf.get("/"), "messages": _UnreadableMessages()}))

    assert html == "[0]"


def test_home_cards_tag_computes_sections_outside_the_home_view(rf):
    from django.template import Context, Template

    request = rf.get("/ro/")
    request.user = SimpleNamespace(role="ADMIN", is_authenticated=True)

    html = Template("{% load navigation %}{% role_home_cards %}").render(
        Context({"request": request})
    )

    assert re.findall(r'class="card__title"><a href="([^"]+)"', html) == ["/ro/admin/"]
