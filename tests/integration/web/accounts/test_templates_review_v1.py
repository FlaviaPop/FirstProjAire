"""Story 1.2 code review v1: shared UI primitives (ISS-001), cool-off text from the setting
(ISS-002) and the username maxlength (ISS-003)."""

import datetime
import re
from pathlib import Path

import pytest
from django.conf import settings

from tests.factories.accounts import StudentFactory

pytestmark = pytest.mark.django_db
TEMPLATES = Path(settings.BASE_DIR) / "src/infrastructure/web/templates/accounts"
WRONG = "wrong-pass-1"


def _lock_out(client, url):
    StudentFactory(username="ana")
    for _ in range(4):
        client.post(url, {"username": "ana", "password": WRONG})
    response = client.post(url, {"username": "ana", "password": WRONG})
    assert response.status_code == 429
    return response.content.decode()


# --- ISS-001: icon and button come from Story 1.5's primitives ------------------------------


@pytest.mark.parametrize("name", ["login.html", "locked_out.html"])
def test_templates_use_the_icon_primitive_not_raw_svg(name):
    source = (TEMPLATES / name).read_text()

    assert "{% ui_icon" in source
    assert "<svg" not in source


def test_login_submit_uses_the_button_primitive():
    source = (TEMPLATES / "login.html").read_text()

    assert "{% ui_button" in source
    assert "<button" not in source


def test_login_page_renders_primitive_markup(client):
    content = client.get("/en/accounts/login/").content.decode()

    button = re.search(
        r'<button type="submit" class="button button--primary"[^>]*>.*?</button>', content, re.S
    )
    assert button, "primary submit button from ui_button"
    assert '<span class="button__label">Sign in</span>' in button.group(0)
    assert re.search(
        r'<svg class="icon icon--32"[^>]*focusable="false"[^>]*aria-hidden="true"', content
    )
    assert "#sign-in-duotone" in content


def test_lockout_page_renders_the_lock_icon_primitive(client):
    content = _lock_out(client, "/en/accounts/login/")

    assert re.search(r'<svg class="icon icon--32"[^>]*aria-hidden="true"', content)
    assert "#lock-simple-duotone" in content


# --- ISS-002: the lockout text follows AXES_COOLOFF_TIME, in both languages ----------------


@pytest.mark.parametrize(
    ("minutes", "url", "expected"),
    [
        (15, "/en/accounts/login/", "Try again in 15 minutes or ask the administrator."),
        (30, "/en/accounts/login/", "Try again in 30 minutes or ask the administrator."),
        (1, "/en/accounts/login/", "Try again in 1 minute or ask the administrator."),
        (15, "/ro/accounts/login/", "Încearcă din nou peste 15 minute"),
        (30, "/ro/accounts/login/", "Încearcă din nou peste 30 de minute"),
        (1, "/ro/accounts/login/", "Încearcă din nou peste 1 minut "),
    ],
)
def test_lockout_message_uses_the_configured_cool_off(
    client, settings, minutes, url, expected, compiled_catalogues
):
    settings.AXES_COOLOFF_TIME = datetime.timedelta(minutes=minutes)

    assert expected in _lock_out(client, url)


# --- ISS-003: username input keeps the form field's maxlength ------------------------------


def test_username_input_has_maxlength_150(client):
    content = client.get("/en/accounts/login/").content.decode()

    username = re.search(r'<input id="id_username"[^>]*>', content).group(0)
    assert 'maxlength="150"' in username
