"""Story 1.6: the sign-in and error pages (Stories 1.1/1.2) load the primitives' stylesheets.

User decision 2026-10-22 ("Add the links now"): layouts/base.html links the component CSS those
pages use, so their class hooks (login-card, form-banner--error, field-error, error-card) are
styled today. ui.js stays out of the base layout until Story 1.7.
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

    assert links == [
        "/static/css/tokens.css",
        *(f"/static/css/components/{name}.css" for name in BASE_STYLESHEETS[1:]),
    ]


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
def test_base_layout_loads_no_script_until_story_1_7(client, path):
    html = client.get(path).content.decode()

    assert "<script" not in html
