"""Story 1.7: role homes and the shared layout (base.html, top bar, messages)."""

import os
import re

import pytest
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db import connection
from django.shortcuts import redirect
from django.test.utils import CaptureQueriesContext
from django.urls import path

from config.urls import urlpatterns as root_urlpatterns
from tests.factories.accounts import UserFactory

pytestmark = pytest.mark.django_db
COMPONENTS_CSS = finders.find("css/components/alert.css")


def _add_message_and_redirect(request):
    messages.success(request, "Saved")
    return redirect("/en/")


def _add_every_level_and_redirect(request):
    for level in (messages.DEBUG, messages.INFO, messages.WARNING, messages.ERROR):
        messages.add_message(request, level, f"level-{level}")
    return redirect("/en/")


# Used only by the flash-message tests via @pytest.mark.urls(__name__).
urlpatterns = [
    path("add-message", _add_message_and_redirect),
    path("add-every-level", _add_every_level_and_redirect),
    *root_urlpatterns,
]


# --- Story Tests block ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fixture", "template", "theme"),
    [
        ("student_client", "home/student.html", "theme-student"),
        ("teacher_client", "home/teacher.html", "theme-staff"),
        ("parent_client", "home/parent.html", "theme-staff"),
        ("admin_client", "home/admin.html", "theme-staff"),
    ],
)
def test_each_role_gets_its_home_and_theme(request, fixture, template, theme):
    response = request.getfixturevalue(fixture).get("/en/")

    assert response.status_code == 200
    assert template in [t.name for t in response.templates]
    assert f'class="{theme}"' in response.content.decode()


def test_anonymous_is_redirected_to_login(client):
    assert client.get("/ro/")["Location"] == "/ro/accounts/login/?next=/ro/"


def test_greeting_uses_first_name(client):
    client.force_login(UserFactory(role="STUDENT", full_name="Ana Maria Pop"))

    assert "Hello, Ana!" in client.get("/en/").content.decode()


def test_role_without_sections_sees_empty_state(teacher_client):
    html = teacher_client.get("/en/").content.decode()

    assert "Your tools will appear here as they become available." in html


def test_layout_has_skip_link_first_and_no_inline_scripts(student_client):
    html = student_client.get("/en/").content.decode()
    body = html.split("<body", 1)[1]

    assert body.index('class="skip-link"') < body.index("<nav")
    assert not re.search(r"<script(?![^>]*\bsrc=)", html)
    assert "style=" not in html
    assert "<style" not in html
    assert 'name="htmx-config"' in html
    assert '"allowEval":false' in html


@pytest.mark.urls(__name__)
def test_flash_message_rendered_once(student_client):
    first = student_client.get("/add-message", follow=True).content.decode()
    second = student_client.get("/en/").content.decode()

    assert "Saved" in first
    assert 'role="status"' in first
    assert "Saved" not in second


# --- AC 1: base layout ----------------------------------------------------------------------------


def test_base_links_tokens_every_component_stylesheet_and_layout(student_client):
    html = student_client.get("/en/").content.decode()
    links = re.findall(r'<link rel="stylesheet" href="([^"]+)">', html)
    components_dir = os.path.dirname(COMPONENTS_CSS)

    expected = {f"/static/css/components/{n}" for n in os.listdir(components_dir)}

    assert links[0] == "/static/css/tokens.css"
    assert links[-1] == "/static/css/layout.css"
    assert set(links[1:-1]) == expected


def test_base_loads_vendored_htmx_deferred_and_ui_js_as_module(student_client):
    html = student_client.get("/en/").content.decode()

    assert '<script src="/static/js/htmx.min.js" defer></script>' in html
    assert '<script type="module" src="/static/js/ui.js"></script>' in html
    assert "https://" not in html.split("<body", 1)[0]


def test_body_sends_the_csrf_token_with_htmx_requests(student_client):
    html = student_client.get("/en/").content.decode()

    assert re.search(
        r'<body class="theme-student" hx-headers=\'\{"X-CSRFToken": "[\w-]+"\}\'>', html
    )


def test_main_is_the_skip_target_and_lang_matches_the_prefix(student_client):
    for lang in ("ro", "en"):
        html = student_client.get(f"/{lang}/").content.decode()

        assert f'<html lang="{lang}">' in html
        assert '<main id="content" tabindex="-1">' in html
        assert '<a class="skip-link" href="#content">' in html


def test_anonymous_pages_use_the_student_theme(client):
    html = client.get("/en/accounts/login/").content.decode()

    assert '<body class="theme-student"' in html


# --- AC 2: messages -------------------------------------------------------------------------------


@pytest.mark.urls(__name__)
def test_message_levels_map_to_alert_levels(student_client, settings):
    settings.MESSAGE_LEVEL = messages.DEBUG

    html = student_client.get("/add-every-level", follow=True).content.decode()

    for level, alert in [(10, "info"), (20, "info"), (30, "warning"), (40, "error")]:
        assert re.search(rf'alert--{alert}"[^>]*>.*?level-{level}<', html, re.S)


# --- AC 3 / 3a: top bar ---------------------------------------------------------------------------


def test_signed_in_top_bar_has_brand_menu_switcher_and_account_menu(client):
    client.force_login(UserFactory(role="TEACHER", full_name="Ion Ionescu"))

    html = client.get("/ro/").content.decode()

    assert re.search(r'<a class="top-bar__brand" href="/ro/">', html)
    assert '<nav class="main-nav" aria-label="Principal">' in html
    assert 'class="lang-switch"' in html
    assert re.search(
        r'<details class="user-menu">\s*<summary[^>]*aria-label="Meniul contului"', html
    )
    assert "Ion Ionescu" in html
    assert "Profesor" in html
    assert re.search(r'<form method="post" action="/ro/accounts/logout/"', html)


def test_anonymous_top_bar_shows_only_brand_and_switcher(client):
    html = client.get("/en/accounts/login/").content.decode()

    assert re.search(r'<a class="top-bar__brand" href="/en/accounts/login/">', html)
    assert 'class="lang-switch"' in html
    assert '<nav class="main-nav"' not in html
    assert "user-menu" not in html


def test_sign_out_posts_and_ends_the_session(student_client):
    response = student_client.post("/en/accounts/logout/")

    assert response.status_code == 302
    assert student_client.get("/en/").status_code == 302


@pytest.mark.parametrize(
    ("fixture", "symbol"),
    [("student_client", "#translate-duotone"), ("teacher_client", '#translate"')],
)
def test_switcher_icon_follows_the_theme(request, fixture, symbol):
    html = request.getfixturevalue(fixture).get("/en/").content.decode()
    switcher = html[html.index('class="lang-switch"') :]

    assert symbol in switcher[: switcher.index("</form>")]


# --- AC 6: home view ------------------------------------------------------------------------------


def test_corrupt_role_gets_403(client):
    client.force_login(UserFactory(role="WIZARD"))

    assert client.get("/en/").status_code == 403


def test_admin_home_shows_the_accounts_card(admin_client):
    html = admin_client.get("/ro/").content.decode()

    assert re.search(r'<a href="/ro/admin/">Conturi</a>', html)


def test_home_render_writes_nothing(student_client):
    student_client.get("/en/")  # first request may set the CSRF cookie

    with CaptureQueriesContext(connection) as queries:
        assert student_client.get("/en/").status_code == 200

    writes = [q["sql"] for q in queries if not q["sql"].lstrip().upper().startswith("SELECT")]
    assert writes == []
