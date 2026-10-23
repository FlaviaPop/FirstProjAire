"""Story 1.6: the sign-in and error pages (Stories 1.1/1.2) load the primitives' stylesheets.

User decision 2026-10-22 ("Add the links now"): layouts/base.html links the component CSS those
pages use, so their class hooks (login-card, form-banner--error, field-error, error-card) are
styled today. Story 1.7 completed the layout: every component stylesheet plus layout.css, and
htmx.min.js / ui.js as external scripts.
"""

import re

import pytest
from django.contrib.staticfiles import finders

pytestmark = pytest.mark.django_db

BASE_STYLESHEETS = ("tokens", "icon", "button", "card", "alert", "form_field")
PAGES = ("/ro/accounts/login/", "/en/accounts/login/", "/ro/does-not-exist/", "/en/does-not-exist/")


def stylesheet_links(html: str) -> list[str]:
    return re.findall(r'<link rel="stylesheet" href="([^"]+)">', html)


@pytest.mark.parametrize("path", PAGES)
def test_login_and_error_pages_link_the_component_stylesheets(client, path):
    html = client.get(path).content.decode()

    links = stylesheet_links(html)

    # Story 1.7 links every component stylesheet; the ones these pages need stay included.
    assert links[0] == "/static/css/tokens.css"
    assert links[-1] == "/static/css/layout.css"
    assert {f"/static/css/components/{name}.css" for name in BASE_STYLESHEETS[1:]} <= set(links)


@pytest.mark.parametrize("name", BASE_STYLESHEETS)
def test_every_base_stylesheet_exists_as_a_static_file(name):
    path = "css/tokens.css" if name == "tokens" else f"css/components/{name}.css"

    assert finders.find(path)


@pytest.mark.parametrize(
    ("path", "status", "hook"),
    [
        ("/ro/accounts/login/", 200, 'class="login-card"'),
        ("/ro/does-not-exist/", 404, 'class="error-card"'),
    ],
)
def test_pages_carry_the_hooks_the_linked_stylesheets_style(client, path, status, hook):
    response = client.get(path)

    assert response.status_code == status
    assert hook in response.content.decode()


def test_wrong_credentials_show_the_styled_error_banner_and_field_hooks(client):
    response = client.post("/en/accounts/login/", {"username": "nobody", "password": "wrong"})
    html = response.content.decode()

    assert 'class="form-banner form-banner--error" role="alert"' in html
    assert "/static/css/components/alert.css" in stylesheet_links(html)


@pytest.mark.parametrize("path", PAGES)
def test_base_layout_loads_only_external_scripts(client, path):
    html = client.get(path).content.decode()

    # Story 1.7: htmx (deferred) and ui.js (module) from /static/; never an inline script.
    assert re.findall(r"<script[^>]*>", html) == [
        '<script src="/static/js/htmx.min.js" defer>',
        '<script type="module" src="/static/js/ui.js">',
    ]
